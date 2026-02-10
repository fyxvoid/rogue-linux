import struct

class Step:
    def __init__(self, op, fail, cmd, wdir, env):
        self.op = op
        self.fail_policy = fail
        self.cmd = cmd
        self.wdir = wdir
        self.env = env
    
    def __repr__(self):
        return f"Step(op={self.op}, cmd='{self.cmd}')"

class PlanReader:
    # Header: magic(8), ver(4), var(4), count(4), strtab(4), reserved(40)
    HEADER_FMT = "<8sIIII40x"
    HEADER_SIZE = 64
    
    # Step: op(4), fail(4), cmd_off(4), cmd_len(4), wdir_off(4), wdir_len(4), env_off(4), env_len(4), reserved(96)
    STEP_FMT = "<IIIIIIII96x"
    STEP_SIZE = 128

    def __init__(self, path):
        with open(path, "rb") as f:
            self.data = f.read()
        
        # Parse Header
        (magic, ver, var, count, strtab_off) = struct.unpack_from(self.HEADER_FMT, self.data, 0)
        self.magic = magic.decode('ascii')
        self.version = ver
        self.variant = var
        self.step_count = count
        self.strtab_offset = strtab_off
        
        self.steps = []
        for i in range(count):
            offset = self.HEADER_SIZE + (i * self.STEP_SIZE)
            self.steps.append(self._parse_step(offset))

    def _parse_step(self, offset):
        (op, fail, c_off, c_len, w_off, w_len, e_off, e_len) = struct.unpack_from(self.STEP_FMT, self.data, offset)
        
        cmd = self._get_str(c_off) # c_len is there, but strtab is null-terminated usually? 
        # plan.h says "null-terminated strings".
        # But planner layout.rs emits length.
        # I'll rely on null termination if length implies it, or just use python decoding.
        # Actually `plan_str` in C Just adds offset. It expects null terminator.
        # Rust `emit_str` adds null terminator.
        
        wdir = self._get_str(w_off)
        env = self._get_str(e_off) if e_len > 0 else None
        
        return Step(op, fail, cmd, wdir, env)

    def _get_str(self, offset):
        # abs offset = strtab_offset + offset
        start = self.strtab_offset + offset
        # Find null terminator
        end = self.data.find(b'\0', start)
        if end == -1: return ""
        return self.data[start:end].decode('utf-8')

