"""Independent bounded program control over the owning-graph reference."""

from reference import EXHAUSTED, INVALID, OK, Reference, word


READY, SUSPENDED, HALTED, FAULTED = range(4)
INTERNAL_FAILURE = 5


class Driver:
    WIDTHS = {14: 5, 15: 2, 16: 2, 17: 1}

    def __init__(self, config, commands):
        self.commands = [list(command) for command in commands]
        self.model = Reference(dict(config, instructionCount=len(self.commands)))
        self.pc = 0
        self.phase = READY

    def observe(self):
        return {"pc": self.pc, "phase": self.phase, "state": self.model.observe()}

    def _fault(self, status):
        self.model.status = status
        self.model.reply = 0
        self.phase = FAULTED

    def run(self, quantum):
        if not word(quantum):
            raise ValueError("quantum must be a u32")
        if quantum == 0 or self.phase in (HALTED, FAULTED):
            return self.observe()
        self.phase = READY
        for _ in range(quantum):
            if self.pc >= len(self.commands):
                self._fault(INTERNAL_FAILURE)
                break
            command = self.commands[self.pc]
            if len(command) > 8 or not all(word(value) for value in command):
                self._fault(INVALID)
                break
            command = command + [0] * (8 - len(command))
            opcode, a, b, c, d, _, _, _ = command
            if opcode not in self.WIDTHS:
                observed = self.model.step(command)
                if observed[0] != OK:
                    self.phase = SUSPENDED if observed[0] == EXHAUSTED else FAULTED
                    break
                self.pc = observed[1] if opcode == 11 else self.pc + 1
                continue
            if any(command[self.WIDTHS[opcode]:]):
                self._fault(INVALID)
                break
            if opcode == 14:
                if c >= len(self.commands) or d >= len(self.commands):
                    self._fault(INVALID)
                    break
                observed = self.model.step([12, a])
                if observed[0] != OK:
                    self.phase = FAULTED
                    break
                self.pc = c if observed[1] == b else d
                self.model.reply = 0
            elif opcode == 15:
                if a >= len(self.commands):
                    self._fault(INVALID)
                    break
                self.model.status = OK
                self.model.reply = 0
                self.pc = a
            elif opcode == 16:
                observed = self.model.step([12, a])
                self.phase = HALTED if observed[0] == OK else FAULTED
                break
            else:
                self.model.status = OK
                self.model.reply = 0
                self.pc += 1
                self.phase = SUSPENDED
                break
        else:
            self.phase = SUSPENDED
        self.model.audit()
        return self.observe()
