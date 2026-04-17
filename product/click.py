from click_up import ClickUp
from click_up.views import ClickWebhook
from Admin import settings
from .models import Booking
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

click_up = ClickUp(
    service_id=settings.CLICK_SERVICE_ID,
    merchant_id=settings.CLICK_MERCHANT_ID,
    secret_key=settings.CLICK_SECRET_KEY   # 🔥 SHART
)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def create_payment_link(request, booking_id):
    try:
        booking = Booking.objects.get(id=booking_id, user=request.user)

        paylink = click_up.initializer.generate_pay_link(
            id=booking.id,
            amount=float(booking.payment),
            return_url=f"https://mazzajoy.uz/api/payment-success/{booking.id}/"
        )

        return Response({
            "success": True,
            "paylink": paylink
        })

    except Booking.DoesNotExist:
        return Response({
            "success": False,
            "message": "Booking topilmadi"
        }, status=404)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def booking_detail(request, pk):
    try:
        booking = Booking.objects.get(id=pk, user=request.user)

        return Response({
            "id": booking.id,
            "status": booking.status,
            "is_paid": booking.is_paid,
            "amount": str(booking.payment)
        })
    except Booking.DoesNotExist:
        return Response({"error": "Not found"}, status=404)

@api_view(['GET'])
# @permission_classes([IsAuthenticated])
def create_payment_link(request, booking_id):
    booking = Booking.objects.get(id=booking_id)

    paylink = click_up.initializer.generate_pay_link(
        id=booking.id,
        amount=float(booking.payment),
        return_url=f"/api/payment-success/{booking.id}/"
    )

    return Response({
        "paylink": paylink
    })
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
@method_decorator(csrf_exempt, name='dispatch')
class ClickWebhookAPIView(ClickWebhook):
    def get(self, request, *args, **kwargs):
        return Response({"status": "ok"})
    def validate_fiscal_item(self, fiscal_item):
        required_fields = ["Name", "SPIC", "PackageCode", "Price", "Count", "VAT"]

        # 1. required fieldlar borligini tekshir
        for field in required_fields:
            if field not in fiscal_item:
                return False

        # 2. Name tekshir (bo‘sh emas)
        if not fiscal_item["Name"] or not str(fiscal_item["Name"]).strip():
            return False

        # 3. SPIC tekshir (string va uzunligi)
        if not isinstance(fiscal_item["SPIC"], str) or len(fiscal_item["SPIC"]) < 5:
            return False

        # 4. PackageCode tekshir
        if not fiscal_item["PackageCode"] or not str(fiscal_item["PackageCode"]).strip():
            return False

        # 5. Price tekshir
        try:
            price = float(fiscal_item["Price"])
            if price <= 0:
                return False
        except:
            return False

        # 6. Count tekshir
        try:
            count = int(fiscal_item["Count"])
            if count <= 0:
                return False
        except:
            return False

        # 7. VAT tekshir (0 yoki 12)
        if fiscal_item["VAT"] not in [0, 12]:
            return False

        return True

    def get_fiscal_items_for_account(self, account):
        try:
            booking = Booking.objects.get(id=account.id)

            return [
                {
                    "Name": f"Booking #{booking.id}",
                    "SPIC": "06102001001000000",  # vaqtincha shu qo'y
                    "PackageCode": f"booking_{booking.id}",
                    "Price": float(booking.payment),
                    "Count": 1,
                    "VAT": 0
                }
            ]
        except Booking.DoesNotExist:
            return []

    
    
    def successfully_payment(self, params):
        """
        Handle successful payments from Click
        """
        # logger.info(f"Successfully payment received - incoming params: {params}")

        booking_id = getattr(params, 'merchant_trans_id', None)

        if booking_id:
            try:
                booking = Booking.objects.get(id=int(booking_id))
                booking.is_paid = True
                booking.status = 'Tasdiqlangan'
                booking.save()
                user = booking.user

            except Booking.DoesNotExist:
              
                pass

    def cancelled_payment(self, params):
        """
        Handle cancelled payments from Click
        """
        # logger.warning(f"Payment cancelled - incoming params: {params}")

        booking_id = getattr(params, 'merchant_trans_id', None)

        if booking_id:
            try:
                booking = Booking.objects.get(id=int(booking_id))
                booking.is_paid = False
                booking.save()

                # logger.warning(f"Order {order_id} marked as payment cancelled")

            except Booking.DoesNotExist:
                # logger.error(f"Booking {booking_id} not found")
                pass
 

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def payment_success(request, order_id):
    try:
        order = Booking.objects.get(id=order_id, user=request.user)

        return Response({
            "success": True,
            "message": "To'lov muvaffaqiyatli",
            "data": {
                "id": order.id,
                "status": order.status,
                "is_paid": order.is_paid,
                "amount": str(order.payment)
            }
        })

    except Booking.DoesNotExist:
        return Response({
            "success": False,
            "message": "Booking topilmadi"
        }, status=404)
