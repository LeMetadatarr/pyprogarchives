"""Example 02 — stream the whole band index lazily.

Run::

    python examples/02_stream_all.py
"""
import itertools

import pyprogarchives as pa


def main() -> None:
    print("First 25 bands across the whole index:")
    for b in itertools.islice(pa.iter_artists(), 25):
        print(f"  {b.display_name:<34} {b.genre or '':<22} {b.country or ''}")


if __name__ == "__main__":
    main()
