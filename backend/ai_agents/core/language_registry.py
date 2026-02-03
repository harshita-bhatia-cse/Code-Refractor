from backend.ai_agents.metrics.python_metrics import PythonMetrics
from backend.ai_agents.metrics.java_metrics import JavaMetrics
from backend.ai_agents.metrics.js_metrics import JSMetrics
from backend.ai_agents.metrics.ts_metrics import TSMetrics
from backend.ai_agents.metrics.c_metrics import CMetrics
from backend.ai_agents.metrics.cpp_metrics import CPPMetrics
from backend.ai_agents.metrics.csharp_metrics import CSharpMetrics
from backend.ai_agents.metrics.go_metrics import GoMetrics
from backend.ai_agents.metrics.php_metrics import PHPMetrics
from backend.ai_agents.metrics.rust_metrics import RustMetrics

REGISTRY = {
    "python": PythonMetrics(),
    "java": JavaMetrics(),
    "javascript": JSMetrics(),
    "typescript": TSMetrics(),
    "c": CMetrics(),
    "cpp": CPPMetrics(),
    "csharp": CSharpMetrics(),
    "go": GoMetrics(),
    "php": PHPMetrics(),
    "rust": RustMetrics(),
}

def get(language):
    return REGISTRY.get(language)
