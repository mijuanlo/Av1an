import os
import re

from Av1an.arg_parse import Args
from Chunks.chunk import Chunk
from Av1an.commandtypes import MPCommands, CommandPair, Command
from Encoders.encoder import Encoder
from Av1an.utils import list_index_of_regex, terminate


class Vpx(Encoder):

    def __init__(self):
        super().__init__(
            encoder_bin='vpxenc',
            encoder_help='vpxenc --help',
            default_args=['--codec=vp9', '--threads=4', '--cpu-used=0', '--end-usage=q', '--cq-level=30'],
            default_passes=2,
            default_q_range=(25, 50),
            output_extension='ivf'
        )

    def compose_1_pass(self, a: Args, c: Chunk, output: str) -> MPCommands:
        return [
            CommandPair(
                Encoder.compose_ffmpeg_pipe(a),
                ['vpxenc', '--passes=1', *a.video_params, '-o', output, '-']
            )
        ]

    def compose_2_pass(self, a: Args, c: Chunk, output: str) -> MPCommands:
        return [
            CommandPair(
                Encoder.compose_ffmpeg_pipe(a),
                ['vpxenc', '--passes=2', '--pass=1', *a.video_params, f'--fpf={c.fpf}', '-o', os.devnull, '-']
            ),
            CommandPair(
                Encoder.compose_ffmpeg_pipe(a),
                ['vpxenc', '--passes=2', '--pass=2', *a.video_params, f'--fpf={c.fpf}', '-o', output, '-']
            )
        ]

    def man_q(self, command: Command, q: int) -> Command:
        """Return command with new cq value

        :param command: old command
        :param q: new cq value
        :return: command with new cq value"""

        adjusted_command = command.copy()

        i = list_index_of_regex(adjusted_command, r"--cq-level=.+")
        adjusted_command[i] = f'--cq-level={q}'

        return adjusted_command

    def match_line(self, line: str):
        """Extract number of encoded frames from line.

        :param line: one line of text output from the encoder
        :return: match object from re.search matching the number of encoded frames"""

        if 'fatal' in line.lower():
            print('\n\nERROR IN ENCODING PROCESS\n\n', line)
            terminate()
        if 'Pass 2/2' in line or 'Pass 1/1' in line:
            return re.search(r"frame.*?/([^ ]+?) ", line)
