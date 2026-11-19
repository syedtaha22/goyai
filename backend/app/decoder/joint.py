import torch
import torch.nn as nn
import torch.nn.functional as F

from app.decoder.modeling import KVCache, Transformer


class JointTransformer(Transformer):
    """
    The transformer of one model that writes an Urdu sentence and then its English sentence.

    The vocabulary holds the Urdu pieces first and the English pieces after them. The Urdu pieces
    and the end token share the tied embedding matrix as output matrix, and the English pieces have
    an output matrix of their own.

    Args:
        vocab_size: Number of tokens, the Urdu and the English pieces together.
        d_model: Hidden width, a multiple of the head width.
        n_layers: Number of blocks.
        max_len: Number of positions.
        english_vocab: Number of English pieces, the last ones of the vocabulary.
    """

    def __init__(
        self, vocab_size: int, d_model: int, n_layers: int, max_len: int, english_vocab: int
    ) -> None:
        super().__init__(vocab_size, d_model, n_layers, max_len)
        self.english_vocab = english_vocab
        self.english_head = nn.Linear(d_model, english_vocab, bias=False)

    @property
    def urdu_vocab(self) -> int:
        """
        Number of Urdu pieces, which is also the id of the first English piece.
        """
        return self.embed.num_embeddings - self.english_vocab

    @classmethod
    def from_state_dict(cls, state: dict[str, torch.Tensor]) -> "JointTransformer":
        """
        Build a model whose shape is read from the weights, and load them.
        """
        vocab_size, d_model = state["embed.weight"].shape
        n_layers = 1 + max(int(k.split(".")[1]) for k in state if k.startswith("blocks."))
        model = cls(
            vocab_size,
            d_model,
            n_layers,
            state["pos.weight"].shape[0],
            state["english_head.weight"].shape[0],
        )
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

        hidden = self.norm(x[:, -1:])
        tied = F.linear(hidden, self.embed.weight)
        logits = torch.cat([tied[..., : -self.english_vocab], self.english_head(hidden)], dim=-1)

        return logits[:, 0], present


@torch.inference_mode()
def write_english(model: JointTransformer, prompt: list[int], end: int, max_new: int) -> list[int]:
    """
    Greedy English continuation of a prompt that ends with the marker between the two sentences.

    Args:
        model: The decoder.
        prompt: Prompt, Urdu sentence and marker token ids.
        end: End-of-sentence token id.
        max_new: Maximum number of generated tokens.

    Returns:
        The ids of the English pieces, offset by the number of Urdu pieces, without the end token.
    """
    device = next(model.parameters()).device
    first = model.urdu_vocab
    logits, cache = model(torch.tensor([prompt], device=device))
    written: list[int] = []

    for _ in range(max_new):
        english = logits[0, first:]
        best = int(english.argmax())

        if logits[0, end] > english[best]:
            break

        written.append(first + best)
        logits, cache = model(torch.tensor([[first + best]], device=device), cache)

    return written
