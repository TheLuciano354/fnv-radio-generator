"""Radio engine: walks a station's dialogue graph the way the game does.

Conditions decide which lines are valid, result scripts update the quest
variables, and when no choice is left the conversation ends and the station
starts again at RadioHello.
"""
import operator
import random
import re

OPS = {"==": operator.eq, "!=": operator.ne, ">": operator.gt,
       ">=": operator.ge, "<": operator.lt, "<=": operator.le}
START_TOPIC = "RadioHello"
SET_RE = re.compile(r"set\s+(?:\w+\.)?(\w+)\s+to\s+(.+?);?\s*$", re.I)
SAFE_EXPR = re.compile(r"^[\d.\s+\-*/()]+$")


class GameProfile:
    """State of the player's game. Anything not listed counts as 0 / not done / alive."""

    def __init__(self, values=None, perks=()):
        self.values = dict(values or {})
        self.perks = set(perks)

    def get(self, function, args):
        if function == "HasPerk":
            return 1.0 if args in self.perks else 0.0
        return float(self.values.get(f"{function}({args})", self.values.get(args, 0.0)))


class RadioStation:
    def __init__(self, data, profile=None, seed=None, fix_bugs=True, avoid_repeated_lines=True):
        self.quest = data["quest"]
        self.topics = data["topics"]
        self.vars = {name: 0.0 for name in data["quest_variables"].values()}
        self.profile = profile or GameProfile()
        self.rng = random.Random(seed)
        self.fix_bugs = fix_bugs
        # Not in the game: don't repeat a spoken line inside one conversation.
        self.avoid_repeated_lines = avoid_repeated_lines
        self._said = set()

    # -- conditions -------------------------------------------------------
    def _value(self, cond):
        args = cond["args"]
        if cond["function"] == "GetQuestVariable" and args.startswith(self.quest + "."):
            return self.vars.get(args.split(".", 1)[1], 0.0)
        return self.profile.get(cond["function"], args)

    def _check(self, cond):
        value = cond["value"] if isinstance(cond["value"], (int, float)) else 0.0
        return OPS[cond["op"]](self._value(cond), value)

    def valid(self, line):
        # A condition flagged OR is grouped with the next one; groups are ANDed.
        group = []
        for cond in line["conditions"]:
            group.append(self._check(cond))
            if not cond["or"]:
                if not any(group):
                    return False
                group = []
        return not group or any(group)

    # -- selection --------------------------------------------------------
    def candidates(self, topic):
        lines = [l for l in self.topics.get(topic, []) if self.valid(l)]
        if self.avoid_repeated_lines:
            fresh = [l for l in lines if "song" in l or l["formid"] not in self._said]
            lines = fresh or lines
        return lines

    def pick(self, topic):
        lines = self.candidates(topic)
        if not lines:
            return None
        return self.rng.choice(lines) if "Random" in lines[0]["flags"] else lines[0]

    def run_script(self, script):
        for stmt in script.splitlines():
            stmt = stmt.split(";", 1)[0].strip()
            m = SET_RE.match(stmt)
            if not m or m.group(1) not in self.vars:
                continue
            expr = re.sub(r"[A-Za-z_][\w.]*",
                          lambda t: str(self.vars.get(t.group(0).rsplit(".", 1)[-1], 0.0)), m.group(2))
            if SAFE_EXPR.match(expr):
                self.vars[m.group(1)] = float(eval(expr, {"__builtins__": {}}))

    # -- playback ---------------------------------------------------------
    def conversation(self):
        """Yield the lines of one conversation (one radio block)."""
        self._said.clear()
        line = self.pick(START_TOPIC)
        while line:
            self._said.add(line["formid"])
            yield line
            self.run_script(line["script"])
            options = [t for t in line["choices"] if self.candidates(t)]
            line = self.pick(self.rng.choice(options)) if options else None

    def song_file(self, line):
        return line.get("song_fixed") if self.fix_bugs and "song_fixed" in line else line["song"]
