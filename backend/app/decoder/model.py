import torch
import torch.nn.functional as F
from torch import nn

HEAD_DIM = 64

KVCache = list[tuple[torch.Tensor, torch.Tensor]]


class RMSNorm(nn.Module):
    """
    Root-mean-square layer normalization.
    """

    def __init__(self, dim: int, eps: float = 1e-5) -> None:
        super().__init__()
        self.eps = eps
        self.weight = nn.Parameter(torch.ones(dim))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        scale = torch.rsqrt(x.float().pow(2).mean(-1, keepdim=True) + self.eps)
        return (x.float() * scale).type_as(x) * self.weight


class SwiGLU(nn.Module):
    """
    Gated feed-forward layer.
    """

    def __init__(self, dim: int) -> None:
        super().__init__()
        hidden = int(8 * dim / 3 / 8) * 8
        self.gate = nn.Linear(dim, hidden, bias=False)
        self.up = nn.Linear(dim, hidden, bias=False)
        self.down = nn.Linear(hidden, dim, bias=False)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.down(F.silu(self.gate(x)) * self.up(x))


class CausalAttention(nn.Module):
    """
    Multi-head causal self-attention that reads and extends a key-value cache.
    """

    def __init__(self, dim: int) -> None:
        super().__init__()
        self.n_heads = dim // HEAD_DIM
        self.qkv = nn.Linear(dim, 3 * dim, bias=False)
        self.proj = nn.Linear(dim, dim, bias=False)

    def forward(
        self, x: torch.Tensor, past: tuple[torch.Tensor, torch.Tensor] | None
    ) -> tuple[torch.Tensor, tuple[torch.Tensor, torch.Tensor]]:
        b, length, dim = x.shape
        q, k, v = self.qkv(x).view(b, length, 3, self.n_heads, HEAD_DIM).unbind(2)
        q, k, v = (t.transpose(1, 2) for t in (q, k, v))

        if past is not None:
            k = torch.cat([past[0], k], dim=2)
            v = torch.cat([past[1], v], dim=2)

        # New tokens attend to every cached token, so only a prompt without a cache needs a mask.
        y = F.scaled_dot_product_attention(q, k, v, is_causal=past is None and length > 1)
        y = self.proj(y.transpose(1, 2).reshape(b, length, dim))

        return y, (k, v)


class Block(nn.Module):
    """
    Pre-norm residual block: attention followed by a feed-forward layer.
    """

    def __init__(self, dim: int) -> None:
        super().__init__()
        self.norm1 = RMSNorm(dim)
        self.norm2 = RMSNorm(dim)
        self.mixer = CausalAttention(dim)
        self.mlp = SwiGLU(dim)

    def forward(self, x, past):
        y, present = self.mixer(self.norm1(x), past)
        x = x + y

        return x + self.mlp(self.norm2(x)), present


class Transformer(nn.Module):
    """
    Decoder-only transformer with learned positions and a tied output head.

    Args:
        vocab_size: Number of tokens.
        d_model: Hidden width, a multiple of the head width.
        n_layers: Number of blocks.
        max_len: Number of positions.
    """

    def __init__(self, vocab_size: int, d_model: int, n_layers: int, max_len: int) -> None:
        super().__init__()
        self.max_len = max_len
        self.embed = nn.Embedding(vocab_size, d_model)
        self.pos = nn.Embedding(max_len, d_model)
        self.blocks = nn.ModuleList(Block(d_model) for _ in range(n_layers))
        self.norm = RMSNorm(d_model)

    @classmethod
    def from_state_dict(cls, state: dict[str, torch.Tensor]) -> "Transformer":
        """
        Build a model whose shape is read from the weights, and load them.
        """
        vocab_size, d_model = state["embed.weight"].shape
        n_layers = 1 + max(int(k.split(".")[1]) for k in state if k.startswith("blocks."))
        model = cls(vocab_size, d_model, n_layers, state["pos.weight"].shape[0])
        model.load_state_dict(state)

        return model.eval()

    def forward(
        self, tokens: torch.Tensor, past: KVCache | None = None
    ) -> tuple[torch.Tensor, KVCache]:
        """
        Logits of the last position and the extended cache.

        Args:
            tokens: Token ids of shape (batch, new_length).
            past: The cache from earlier calls, or None for a fresh prompt.
        """
        offset = 0 if past is None else past[0][0].shape[2]
        positions = torch.arange(offset, offset + tokens.shape[1], device=tokens.device)
        x = self.embed(tokens) + self.pos(positions)

        present: KVCache = []
        for i, block in enumerate(self.blocks):
            x, kv = block(x, None if past is None else past[i])
            present.append(kv)

        logits = F.linear(self.norm(x[:, -1:]), self.embed.weight)

        return logits[:, 0], present
