import torch
import torch.nn.functional as F

from app.decoder.model import KVCache, Transformer


@torch.inference_mode()
def beam_search(
    model: Transformer,
    prompt: list[int],
    eos: int,
    *,
    beams: int,
    max_new: int,
    length_alpha: float,
) -> list[list[int]]:
    """
    Beam search that extends a key-value cache, so every step processes one new token per beam.

    Args:
        model: The decoder.
        prompt: Prompt token ids.
        eos: End-of-sentence token id.
        beams: Beam width.
        max_new: Maximum number of generated tokens.
        length_alpha: Exponent of the length normalization of finished sentences.

    Returns:
        Up to 2 * beams generated token id lists (without the prompt), best first.
    """
    device = next(model.parameters()).device
    logits, cache = model(torch.tensor([prompt], device=device))

    active: list[tuple[float, list[int]]] = [(0.0, [])]
    finished: list[tuple[float, list[int]]] = []

    for step in range(max_new):
        top = F.log_softmax(logits.float(), dim=-1).topk(beams, dim=-1)
        values, indices = top.values.tolist(), top.indices.tolist()

        expansions = [
            (score + log_prob, tokens + [token], row)
            for row, (score, tokens) in enumerate(active)
            for log_prob, token in zip(values[row], indices[row], strict=True)
        ]
        expansions.sort(key=lambda expansion: expansion[0], reverse=True)

        active, parents = [], []
        for score, tokens, row in expansions:
            if tokens[-1] == eos:
                finished.append((score / (len(tokens) ** length_alpha), tokens[:-1]))
            else:
                active.append((score, tokens))
                parents.append(row)

            if len(active) == beams:
                break

        if len(finished) >= beams or not active or step == max_new - 1:
            break

        logits, cache = model(
            torch.tensor([[tokens[-1]] for _, tokens in active], device=device),
            reorder(cache, parents, device),
        )

    finished.sort(key=lambda entry: entry[0], reverse=True)
    unfinished = [(score / (len(tokens) ** length_alpha), tokens) for score, tokens in active]

    return [tokens for _, tokens in (finished + unfinished)[: beams * 2]]


def reorder(cache: KVCache, parents: list[int], device: torch.device) -> KVCache:
    """
    The cache rows of the surviving beams, in their new order.
    """
    index = torch.tensor(parents, device=device)

    return [(k.index_select(0, index), v.index_select(0, index)) for k, v in cache]
