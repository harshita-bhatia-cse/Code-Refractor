import json


class JSONMetrics:
    def analyze(self, code: str):
        lines = code.splitlines()
        metrics = {
            "lines": len(lines),
            "objects": 0,
            "arrays": 0,
            "keys": 0,
            "is_valid_json": False,
        }

        try:
            payload = json.loads(code)
            metrics["is_valid_json"] = True
            obj_count, arr_count, key_count = self._walk(payload)
            metrics["objects"] = obj_count
            metrics["arrays"] = arr_count
            metrics["keys"] = key_count
        except Exception:
            pass

        return metrics

    def _walk(self, node):
        if isinstance(node, dict):
            obj_count = 1
            arr_count = 0
            key_count = len(node)
            for value in node.values():
                o, a, k = self._walk(value)
                obj_count += o
                arr_count += a
                key_count += k
            return obj_count, arr_count, key_count

        if isinstance(node, list):
            obj_count = 0
            arr_count = 1
            key_count = 0
            for value in node:
                o, a, k = self._walk(value)
                obj_count += o
                arr_count += a
                key_count += k
            return obj_count, arr_count, key_count

        return 0, 0, 0
