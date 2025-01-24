################################################################################
#
# Copyright (C) 2022-2025 Advanced Micro Devices, Inc. All rights reserved.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
################################################################################

from .Common import printExit
from .TensileInstructions import Instructions as ti

from dataclasses import dataclass, field
from typing import Type

################################################################################
# Memory Instruction
################################################################################
@dataclass
class MemoryInstruction:
    inst: Type[ti.ReadWriteInstruction]
    numAddresses: int
    numOffsets: int
    offsetMultiplier: int
    blockWidth: float
    numBlocks: int = field(init=False)
    totalWidth: float = field(init=False)
    issueLatency: int = field(init=False)

    def __post_init__(self):
        self.numBlocks = 2 if self.numAddresses > 1 or self.numOffsets > 1 else 1
        self.totalWidth = self.blockWidth * self.numBlocks
        self.issueLatency = self.inst.issueLatency()

    def getInst(self, highBits=0):
        if highBits:
            if self.inst is ti.DSLoadU8:
                return ti.DSLoadD16HIU8
            elif self.inst is ti.DSLoadU16:
                return ti.DSLoadD16HIU16
            elif self.inst is ti.DSStoreB16:
                return ti.DSStoreD16HIB16
            elif self.inst is ti.DSStoreB8:
                return ti.DSStoreB8HID16
            else:
                printExit(str(self.inst) + " does not support high bits instructions.")

        return self.inst
