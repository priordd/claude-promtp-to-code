"""Banking service for external payment processing."""

import asyncio
from decimal import Decimal
from typing import Any, Dict, Optional

import httpx
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

from payment_service.config import settings
from payment_service.models.payment import CardData


class BankingService:
    """Service for interacting with external banking APIs."""
    
    def __init__(self):
        self.logger = structlog.get_logger(__name__)
        self.base_url = settings.banking_api_url
        self.timeout = settings.banking_api_timeout
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def authorize_payment(
        self,
        transaction_id: str,
        amount: Decimal,
        currency: str,
        card_data: Optional[CardData],
        correlation_id: str,
    ) -> Dict[str, Any]:
        """Authorize payment with external banking service."""
        self.logger.info(
            "Authorizing payment",
            transaction_id=transaction_id,
            amount=str(amount),
            currency=currency,
            correlation_id=correlation_id,
        )
        
        payload = {
            "transaction_id": transaction_id,
            "amount": float(amount),
            "currency": currency,
        }
        
        if card_data:
            payload.update({
                "card_number": card_data.card_number,
                "expiry_month": card_data.expiry_month,
                "expiry_year": card_data.expiry_year,
                "cvv": card_data.cvv,
                "cardholder_name": card_data.cardholder_name,
            })
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/v1/authorize",
                    json=payload,
                    headers={
                        "Content-Type": "application/json",
                        "X-Correlation-ID": correlation_id,
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    self.logger.info(
                        "Payment authorized successfully",
                        transaction_id=transaction_id,
                        authorization_id=result.get("authorization_id"),
                        correlation_id=correlation_id,
                    )
                    return result
                elif response.status_code == 402:
                    # Payment declined
                    result = response.json()
                    self.logger.warning(
                        "Payment declined",
                        transaction_id=transaction_id,
                        decline_reason=result.get("message"),
                        correlation_id=correlation_id,
                    )
                    return {
                        "status": "declined",
                        "message": result.get("message", "Payment declined"),
                        "decline_code": result.get("decline_code"),
                    }
                else:
                    response.raise_for_status()
                    
        except httpx.TimeoutException:
            self.logger.error(
                "Banking service timeout",
                transaction_id=transaction_id,
                correlation_id=correlation_id,
            )
            raise Exception("Banking service timeout")
        except httpx.RequestError as e:
            self.logger.error(
                "Banking service request error",
                transaction_id=transaction_id,
                error=str(e),
                correlation_id=correlation_id,
            )
            raise Exception(f"Banking service error: {str(e)}")
        except Exception as e:
            self.logger.error(
                "Unexpected banking service error",
                transaction_id=transaction_id,
                error=str(e),
                correlation_id=correlation_id,
            )
            raise
    
    async def capture_payment(
        self,
        authorization_id: str,
        correlation_id: str,
    ) -> Dict[str, Any]:
        """Capture authorized payment."""
        self.logger.info(
            "Capturing payment",
            authorization_id=authorization_id,
            correlation_id=correlation_id,
        )
        
        payload = {
            "authorization_id": authorization_id,
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/v1/capture",
                    json=payload,
                    headers={
                        "Content-Type": "application/json",
                        "X-Correlation-ID": correlation_id,
                    }
                )
                
                response.raise_for_status()
                result = response.json()
                
                self.logger.info(
                    "Payment captured successfully",
                    authorization_id=authorization_id,
                    capture_id=result.get("capture_id"),
                    correlation_id=correlation_id,
                )
                
                return result
                
        except httpx.TimeoutException:
            self.logger.error(
                "Banking service timeout during capture",
                authorization_id=authorization_id,
                correlation_id=correlation_id,
            )
            raise Exception("Banking service timeout")
        except httpx.RequestError as e:
            self.logger.error(
                "Banking service capture error",
                authorization_id=authorization_id,
                error=str(e),
                correlation_id=correlation_id,
            )
            raise Exception(f"Banking service error: {str(e)}")
    
    async def process_refund(
        self,
        transaction_id: str,
        amount: Decimal,
        correlation_id: str,
    ) -> Dict[str, Any]:
        """Process refund with external banking service."""
        self.logger.info(
            "Processing refund",
            transaction_id=transaction_id,
            amount=str(amount),
            correlation_id=correlation_id,
        )
        
        payload = {
            "transaction_id": transaction_id,
            "amount": float(amount),
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/v1/refund",
                    json=payload,
                    headers={
                        "Content-Type": "application/json",
                        "X-Correlation-ID": correlation_id,
                    }
                )
                
                response.raise_for_status()
                result = response.json()
                
                self.logger.info(
                    "Refund processed successfully",
                    transaction_id=transaction_id,
                    refund_id=result.get("refund_id"),
                    correlation_id=correlation_id,
                )
                
                return result
                
        except httpx.TimeoutException:
            self.logger.error(
                "Banking service timeout during refund",
                transaction_id=transaction_id,
                correlation_id=correlation_id,
            )
            raise Exception("Banking service timeout")
        except httpx.RequestError as e:
            self.logger.error(
                "Banking service refund error",
                transaction_id=transaction_id,
                error=str(e),
                correlation_id=correlation_id,
            )
            raise Exception(f"Banking service error: {str(e)}")
    
    async def health_check(self) -> bool:
        """Check banking service health."""
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(f"{self.base_url}/health")
                return response.status_code == 200
        except Exception as e:
            self.logger.warning("Banking service health check failed", error=str(e))
            return False