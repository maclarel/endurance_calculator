# Race Strategy Planner 

A small Tkinter desktop tool for planning and iterating an endurance race pit/energy/tire strategy.

## What it does

- Generates an initial pit/strategy plan from baseline race parameters.
- Lets you “recalculate” mid-race by entering current progress (laps completed, extra pit time, updated lap time, etc.).
- Produces a step-by-step strategy log including pit windows and (when applicable) warnings when tire wear exceeds a +15% expected lifespan margin.

## How to run

You can download the Windows executable from the [Releases](https://github.com/maclarel/endurance_calculator/releases) page, or run the Python code directly if you have Python installed.

```bash
python main.py
```

## How to use

### 1) Set up the baseline race

In **1. Global Setup**:

- **Race Length (min)**: Total race duration.
- **Base Lap Time (s)**: Your expected average lap time.
- **Energy Cap**: Max usable energy/fuel/VE (%) available per stint.
- **Energy/Lap**: Consumption per lap (same unit basis as Energy Cap).
- **Tire Life (laps)**: How many laps a tire set is expected to last.
- **Total Tires (All)**: Total tires available for the event (including the starting set).
- **Fuel Stop Time (s)**: Time loss for an energy-only stop.
- **Fuel + Tires Time (s)**: Time loss for an energy + tire stop.

Click **Generate Initial Plan** to produce the initial strategy log.

### 2) During the race: update live state

In **2. Live Adjustments**:

- **Laps Completed**: Your current lap count.
- **Extra Pit Time (s)**: Any additional stationary/slow time not captured by the standard pit stop times (repairs, penalties, long FCY service, etc.).
- **Adj Lap Time (s)**: Updated expected lap time for the remainder (traffic/night/rain).
- **Adj Energy/Lap**: Updated consumption rate.
- **Adj Tire Life**: Updated tire life expectation.
- **Tires Rem. in Garage**: Tires remaining *in the garage* (not including what’s on the car).  
  - This is usually `Total Tires (All) - 4` at the start.

### 3) Tactical overrides (optional)

In **3. Tactical Overrides**:

- **Strict Tire Life (No 15% Margin)**:
  - Off (default): the planner allows a ~15% margin beyond `Tire Life` before flagging risk.
  - On: the planner treats `Tire Life` as a hard limit (more conservative).
- **Manual Time Rem. (min)**:
  - Leave blank to have remaining time computed from race length, laps completed, lap time, and extra pit time.
  - Fill in to override remaining time directly (useful if race control/strategy calls change the effective remaining time).

Click **Apply & Recalculate** to append a recalculated plan to the strategy log.

## Understanding the output

The **Strategy Log** shows:

- A stint header and an estimated total lap count for the remainder.
- For each planned stop:
  - The lap to pit on
  - Whether to take **VE ONLY** (energy only) or **VE + TIRES**
  - Tires remaining in the garage after that action
  - A **Pit Window** time marker (driving + pit overhead) for when the stop should occur
- A final **FINISH** summary line.

If you see a red warning:

- `WARNING: TIRE WEAR EXCEEDS MARGIN ON NEXT STINT`
- This indicates the planned next stint pushes beyond the tire-life margin (depending on strict mode). You may need to adjust tire life, add swaps (if tires available), or revise stint lengths.

## Notes / limitations

- Results are only as good as the assumptions you input (lap time, consumption, tire life, pit loss).
- There are probably bugs. Pull requests fixing them are welcome.
