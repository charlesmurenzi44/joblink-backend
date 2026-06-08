import logging
import uuid

from django.conf import settings

from .models import MoMoTransaction

logger = logging.getLogger(__name__)


class MoMoError(Exception):
    pass


def momo_configured() -> bool:
    return bool(
        getattr(settings, 'MTN_MOMO_API_USER', '')
        and getattr(settings, 'MTN_MOMO_API_KEY', '')
        and getattr(settings, 'MTN_MOMO_SUBSCRIPTION_KEY', '')
    )


def _normalize_amount(amount) -> float:
    return float(amount or 0)


def _create_tx(job, tx_type, phone, amount):
    reference = f'JL-{job.id}-{tx_type[:3]}-{uuid.uuid4().hex[:8]}'
    return MoMoTransaction.objects.create(
        job=job,
        transaction_type=tx_type,
        amount=_normalize_amount(amount),
        phone=phone,
        reference=reference,
    )


def request_collection(job, phone: str, amount) -> MoMoTransaction:
    """Request payment from client (escrow collection)."""
    tx = _create_tx(job, 'collection', phone, amount)

    if not momo_configured():
        tx.status = 'success'
        tx.response = {'mode': 'simulated', 'message': 'MoMo not configured'}
        tx.save(update_fields=['status', 'response'])
        logger.info('MoMo collection simulated for job %s', job.id)
        return tx

    try:
        # MTN MoMo Collection API placeholder — wire credentials in production.
        tx.external_id = uuid.uuid4().hex
        tx.status = 'pending'
        tx.response = {'message': 'Collection initiated — confirm on phone'}
        tx.save(update_fields=['external_id', 'status', 'response'])
    except Exception as exc:
        tx.status = 'failed'
        tx.response = {'error': str(exc)}
        tx.save(update_fields=['status', 'response'])
        raise MoMoError(str(exc)) from exc

    return tx


def request_disbursement(job, phone: str, amount) -> MoMoTransaction:
    """Pay worker after job completion."""
    tx = _create_tx(job, 'disbursement', phone, amount)

    if not momo_configured():
        tx.status = 'success'
        tx.response = {'mode': 'simulated', 'message': 'MoMo not configured'}
        tx.save(update_fields=['status', 'response'])
        logger.info('MoMo disbursement simulated for job %s', job.id)
        return tx

    try:
        tx.external_id = uuid.uuid4().hex
        tx.status = 'pending'
        tx.response = {'message': 'Disbursement initiated'}
        tx.save(update_fields=['external_id', 'status', 'response'])
    except Exception as exc:
        tx.status = 'failed'
        tx.response = {'error': str(exc)}
        tx.save(update_fields=['status', 'response'])
        raise MoMoError(str(exc)) from exc

    return tx
