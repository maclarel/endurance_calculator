import math


def calculate_strategy(rem_mins, lap_time, e_per_lap, t_life, tires_in_garage,
                       energy_cap=100.0, strict=False,
                       pit_energy_secs=60.0, pit_tires_secs=72.0,
                       start_lap=0):
    """
    Compute the race strategy plan without any UI concerns.

    Returns a list of dicts — one per pit stop plus a terminal 'finish' entry:
      stop:   type, lap, stint_num, max_stint_laps, action, tires_left,
              danger, display_secs
      finish: type, lap (total race laps), laps_to_fin, tires_remaining
    """
    total_rem_secs = rem_mins * 60
    driving_secs = 0   # driving time only — controls loop/finish (no pit overhead)
    display_secs = 0   # driving + pit overhead — used for Pit Window display
    current_lap = start_lap
    tires_left = tires_in_garage
    laps_on_current_set = 0
    stint_num = 1

    max_stint_laps = max(1, math.floor(energy_cap / e_per_lap))
    limit = t_life if strict else (t_life * 1.15)

    # Number of full-energy stints that fit in the remaining race time.
    # Uses driving time only so it exactly matches the loop iteration count.
    estimated_stops = math.floor(total_rem_secs / (max_stint_laps * lap_time))

    # How many consecutive stints can one set of tires cover?
    stints_per_set = max(1, math.floor(limit / max_stint_laps))

    # Required positions: the exact stop indices where tire life demands a change.
    # First required stop is at index (stints_per_set − 1), then every
    # stints_per_set steps after that.
    required_positions = list(range(stints_per_set - 1, estimated_stops, stints_per_set))
    n_required = len(required_positions)

    # Never plan more swaps than tire life requires, even if extra tires are available.
    available_swaps = tires_in_garage // 4  # 4 tires per set
    planned_swaps = min(n_required, available_swaps)

    # Distribute planned_swaps among required_positions using centred Bresenham.
    # When inventory is short (planned_swaps < n_required) the skipped required
    # positions generate warnings; centring (start accumulator at 0.5) spreads
    # those missed swaps as evenly as possible rather than bunching them at the
    # start or end of the race.
    swap_needed = [False] * estimated_stops
    if planned_swaps >= n_required:
        for pos in required_positions:
            swap_needed[pos] = True
    elif planned_swaps > 0:
        # Start at 0.5 to centre the distribution: any skipped swaps are placed
        # symmetrically through the race rather than being front- or back-loaded.
        accumulator = 0.5
        ratio = planned_swaps / n_required
        for pos in required_positions:
            accumulator += ratio
            if accumulator >= 1.0:
                swap_needed[pos] = True
                accumulator -= 1.0
    # else: 0 planned swaps — all required positions stay False (warnings only)

    stops = []
    stop_idx = 0

    while driving_secs < total_rem_secs:
        if driving_secs + (max_stint_laps * lap_time) >= total_rem_secs:
            laps_to_fin = math.ceil((total_rem_secs - driving_secs) / lap_time)
            stops.append({
                'type': 'finish',
                'lap': current_lap + laps_to_fin,
                'laps_to_fin': laps_to_fin,
                'tires_remaining': tires_left,
            })
            break

        driving_secs += max_stint_laps * lap_time
        display_secs += max_stint_laps * lap_time
        current_lap += max_stint_laps
        laps_on_current_set += max_stint_laps
        stint_num += 1

        # Use the pre-computed plan directly — no safety override is needed because
        # required_positions already encodes the tire-life constraint precisely.
        should_swap = swap_needed[stop_idx] if stop_idx < len(swap_needed) else False

        # Hard floor: never swap without inventory.
        if should_swap and tires_left < 4:
            should_swap = False

        if should_swap:
            display_secs += pit_tires_secs
            tires_left -= 4
            laps_on_current_set = 0
        else:
            display_secs += pit_energy_secs

        danger = (laps_on_current_set + max_stint_laps) > limit

        stops.append({
            'type': 'stop',
            'lap': current_lap,
            'stint_num': stint_num,
            'max_stint_laps': max_stint_laps,
            'action': 'VE + TIRES' if should_swap else 'VE ONLY',
            'tires_left': tires_left,
            'danger': danger,
            'display_secs': display_secs,
        })
        stop_idx += 1

    return stops
