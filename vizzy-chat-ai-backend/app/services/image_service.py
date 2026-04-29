from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.chat import GeneratePromptRequest
from app.schemas.image import ImageGenerateRequest, ImageGenerateResponseData
from app.services.ai_service import AIService
from app.services.prompt_engine import PromptEngine


class ImageService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.ai_service = AIService()
        self.prompt_engine = PromptEngine(db)

    async def generate_images(self, request: ImageGenerateRequest) -> ImageGenerateResponseData:
        enhanced_prompt = request.prompt
        if request.user_id:
            prompt_bundle = await self.prompt_engine.generate_prompt_bundle(
                GeneratePromptRequest(
                    message=request.prompt,
                    user_type=request.user_type,
                    context=request.context,
                    user_id=request.user_id,
                )
            )
            enhanced_prompt = prompt_bundle.image_prompts[0]

        prepared_request = request.model_copy(update={"prompt": enhanced_prompt})
        result = await self.ai_service.generate_images(prepared_request)
        return result.model_copy(update={"revised_prompt": enhanced_prompt})
