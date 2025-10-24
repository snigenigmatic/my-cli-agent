class Memory:
    def __init__(self):
        self.history = []

    def add(self, role, text):
        self.history.append({"role": role, "text": text})

    def context(self):
        return "\n".join(f"{m['role'].upper()}: {m['text']}" for m in self.history[-8:])
