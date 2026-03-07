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

    # Minimum swaps needed to keep every stint within the tire-life limit.
    n_required = len(range(stints_per_set - 1, estimated_stops, stints_per_set))

    # Never plan more swaps than tire life requires, even if extra tires are available.
    available_swaps = tires_in_garage // 4  # 4 tires per set
    planned_swaps = min(n_required, available_swaps)

    # ---- Block-based swap placement (guarantees no back-to-back warnings) ----
    #
    # Divide estimated_stops into swap blocks of two sizes:
    #   Normal   (size = stints_per_set):     0 warnings, swap at age == stints_per_set
    #   Extended (size = stints_per_set + 1): 1 warning  at age == stints_per_set,
    #                                         then swap   at age == stints_per_set + 1
    #
    # After the last swap there is a short "final run" of at most stints_per_set − 1
    # stops (age stays below the warning threshold → 0 warnings).
    #
    # Because every warning stop is the second-to-last stop of an extended block and
    # is unconditionally followed by a swap, warnings are NEVER consecutive.
    #
    # excess  = stops that cannot be covered by all-normal blocks alone.
    # n3      = number of those that must become extended blocks (the rest go into the
    #           final run, capped at stints_per_set − 1 to stay warning-free).
    excess = max(0, estimated_stops - planned_swaps * stints_per_set)
    n3_extended = min(planned_swaps, max(0, excess - (stints_per_set - 1)))

    # Centred Bresenham: spread n3_extended extended blocks evenly among planned_swaps.
    # Starting accumulator at 0.5 centres the distribution so extended blocks are never
    # bunched at the start or end of the race.
    is_extended = [False] * planned_swaps
    if n3_extended >= planned_swaps:
        is_extended = [True] * planned_swaps
    elif n3_extended > 0:
        accumulator = 0.5
        ratio = n3_extended / planned_swaps
        for i in range(planned_swaps):
            accumulator += ratio
            if accumulator >= 1.0:
                is_extended[i] = True
                accumulator -= 1.0

    # Convert block sequence → a swap_needed boolean array over all stop indices.
    swap_needed = [False] * estimated_stops
    block_pos = 0
    for ext in is_extended:
        block_size = stints_per_set + (1 if ext else 0)
        swap_pos = block_pos + block_size - 1
        if swap_pos < estimated_stops:
            swap_needed[swap_pos] = True
        block_pos += block_size
    # block_pos now points to the start of the final run (length = excess − n3_extended)

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

        # Use the pre-computed plan directly.  The block-based placement above
        # guarantees that every warning stop is immediately followed by a swap,
        # so no safety override is needed here.
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
