"""Stream an audio file to the Sawt API over WebSocket and print the result.

The file is cut into short WAV segments that are sent one by one, the way a live
recorder would send audio. Run from the repository root:

    uv run --project backend python examples/stream_client.py call.wav --translate
"""

import argparse
import asyncio
import io
import json
import os

import websockets
from pydub import AudioSegment


def segments(path: str, seconds: float) -> list[bytes]:
    audio = AudioSegment.from_file(path)
    step = int(seconds * 1000)
    chunks = []
    for start in range(0, len(audio), step):
        buf = io.BytesIO()
        audio[start : start + step].export(buf, format="wav")
        chunks.append(buf.getvalue())
    return chunks


async def reply(ws: websockets.ClientConnection, expected: str) -> dict:
    """Receive the next server message; exit with the server's error if it is not ``expected``."""
    message = json.loads(await ws.recv())
    if message.get("type") != expected:
        raise SystemExit(f"error {message.get('status')}: {message.get('detail')}")
    return message


async def stream(url: str, path: str, translate: bool, chunk_seconds: float) -> dict:
    async with websockets.connect(url, max_size=None) as ws:
        start = {"type": "start", "translate": translate, "filename": os.path.basename(path)}
        await ws.send(json.dumps(start))
        print(await reply(ws, "started"))

        for chunk in segments(path, chunk_seconds):
            await ws.send(chunk)
            ack = await reply(ws, "chunk_ack")
            print(f"  chunk {ack['chunk_number']}: {ack['total_duration_s']:.1f}s received")

        await ws.send(json.dumps({"type": "end"}))
        processing = await reply(ws, "processing")
        print(f"processing {processing['total_duration_s']:.1f}s of audio …")
        return (await reply(ws, "result"))["data"]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("audio", help="path to an audio file")
    parser.add_argument("--translate", action="store_true", help="also return the Arabic version")
    parser.add_argument("--chunk-seconds", type=float, default=5.0)
    parser.add_argument("--url", default="ws://localhost:8000/api/v1/conversations/stream")
    args = parser.parse_args()

    result = asyncio.run(stream(args.url, args.audio, args.translate, args.chunk_seconds))
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
