from .pipeline import run_vinaya_pipeline
from .types import VinayaRequest

sample_request: VinayaRequest = {
    "requestId": "vinaya-demo-001",
    "title": "是否应先试行新的内容治理规则",
    "requestText": "请评估是否应将新的自动内容治理规则直接推广到全部用户。",
    "domain": "content-moderation",
    "riskLevel": "high",
    "context": "当前规则仍处于讨论阶段，存在误伤担忧。",
}

sample_report = run_vinaya_pipeline(sample_request)
