"""Domain services for inventory movements."""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import List, Optional, Tuple, TYPE_CHECKING

from .models import BatchLocation, ItemBatch, Location

if TYPE_CHECKING:
    from .models import Item


@dataclass
class AllocationResult:
    allocated_units: int
    remaining_units: int
    assignments: List[Tuple[Location, int]]


@dataclass
class DeallocationResult:
    removed_units: int
    assignments: List[Tuple[Location, int]]


def _iter_candidate_locations(preferred: Optional[Location]) -> List[Location]:
    locations: List[Location] = []
    if preferred:
        locations.append(preferred)
        other_qs = Location.objects.exclude(id=preferred.id)
    else:
        other_qs = Location.objects.all()
    locations.extend(other_qs.order_by('code'))
    return locations


def allocate_inbound(batch: ItemBatch, quantity: int, preferred: Optional[Location] = None) -> AllocationResult:
    """Assign inbound units across available locations and grow batch stock."""
    units = max(0, int(quantity))
    if units == 0:
        return AllocationResult(0, 0, [])

    batch.quantity_units = batch.quantity_units + units
    batch.save(update_fields=['quantity_units', 'updated_at'])

    assignments: List[Tuple[Location, int]] = []
    remaining = units
    volume_per_unit = batch.item.packaging_volume or Decimal('0')

    for loc in _iter_candidate_locations(preferred):
        if remaining <= 0:
            break
        if volume_per_unit > 0:
            available_volume = Decimal(str(loc.available_volume))
            if available_volume <= 0:
                continue
            max_units_fit = int(available_volume // volume_per_unit)
            if max_units_fit <= 0:
                continue
            assign_units = min(max_units_fit, remaining)
        else:
            assign_units = remaining
        if assign_units <= 0:
            continue
        bl, _ = BatchLocation.objects.get_or_create(batch=batch, location=loc)
        bl.quantity_units = bl.quantity_units + assign_units
        bl.save(update_fields=['quantity_units'])
        assignments.append((loc, assign_units))
        remaining -= assign_units

    return AllocationResult(allocated_units=units - remaining, remaining_units=remaining, assignments=assignments)


def release_outbound(batch: ItemBatch, quantity: int, preferred: Optional[Location] = None) -> DeallocationResult:
    """Release stock for outbound movement, favouring preferred location first."""
    units = max(0, int(quantity))
    if units == 0:
        return DeallocationResult(0, [])
    if units > batch.quantity_units:
        raise ValueError('Not enough stock for outbound')

    target = min(units, batch.quantity_units)
    assignments: List[Tuple[Location, int]] = []
    remaining = target

    def _drain(bl: BatchLocation, wanted: int) -> int:
        take = min(bl.quantity_units, wanted)
        if take <= 0:
            return 0
        bl.quantity_units = bl.quantity_units - take
        if bl.quantity_units <= 0:
            bl.delete()
        else:
            bl.save(update_fields=['quantity_units'])
        assignments.append((bl.location, take))
        return take

    if preferred:
        try:
            bl = BatchLocation.objects.get(batch=batch, location=preferred)
            drained = _drain(bl, remaining)
            remaining -= drained
        except BatchLocation.DoesNotExist:
            pass

    if remaining > 0:
        for bl in BatchLocation.objects.filter(batch=batch).order_by('-quantity_units'):
            drained = _drain(bl, remaining)
            remaining -= drained
            if remaining <= 0:
                break

    removed = target - remaining
    if removed > 0:
        batch.quantity_units = max(0, batch.quantity_units - removed)
        batch.save(update_fields=['quantity_units', 'updated_at'])

    return DeallocationResult(removed_units=removed, assignments=assignments)


def max_placeable_units(item: 'Item', preferred: Optional[Location] = None) -> int:
    per_unit = item.packaging_volume or Decimal('0')
    if per_unit <= 0:
        return 1000000000
    total = 0
    for loc in _iter_candidate_locations(preferred):
        avail = Decimal(str(loc.available_volume))
        if avail <= 0:
            continue
        total += int(avail // per_unit)
    return total

