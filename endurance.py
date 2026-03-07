import tkinter as tk
from tkinter import ttk
import math

class RaceStrategyApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Endurance Race Strategist Pro")
        self.root.geometry("1150x850")
        self.root.minsize(950, 750)

        self.root.columnconfigure(1, weight=1)
        self.root.rowconfigure(0, weight=1)

        # --- State Variables ---
        self.race_length_mins = tk.DoubleVar(value=360) 
        self.lap_time_secs = tk.DoubleVar(value=125.0)  
        self.energy_cap = tk.DoubleVar(value=100.0)
        self.energy_per_lap = tk.DoubleVar(value=9.0)
        self.tire_life_laps = tk.IntVar(value=22)
        self.total_tires_avail = tk.IntVar(value=32) 
        self.pit_energy_secs = tk.DoubleVar(value=35.0)
        self.pit_tires_secs = tk.DoubleVar(value=80.0)
        
        self.laps_completed = tk.IntVar(value=0)
        self.extra_pit_time_secs = tk.DoubleVar(value=0.0)
        self.new_lap_time_secs = tk.DoubleVar(value=125.0)
        self.new_energy_per_lap = tk.DoubleVar(value=9.0)
        self.new_tire_life = tk.IntVar(value=22)
        self.new_tires_remaining = tk.IntVar(value=28) 

        self.strict_tire_mode = tk.BooleanVar(value=False)
        self.manual_rem_mins = tk.StringVar(value="")

        # Syncing
        self.lap_time_secs.trace_add("write", lambda *a: self.sync_var(self.lap_time_secs, self.new_lap_time_secs))
        self.energy_per_lap.trace_add("write", lambda *a: self.sync_var(self.energy_per_lap, self.new_energy_per_lap))
        self.tire_life_laps.trace_add("write", lambda *a: self.sync_var(self.tire_life_laps, self.new_tire_life))
        self.total_tires_avail.trace_add("write", lambda *a: self.new_tires_remaining.set(max(0, self.total_tires_avail.get() - 4)))

        self.setup_ui()

    def sync_var(self, src, dest):
        try: dest.set(src.get())
        except: pass

    def setup_ui(self):
        sidebar = ttk.Frame(self.root, padding="10")
        sidebar.grid(row=0, column=0, sticky="nsew")
        
        # UI Panels
        setup_box = ttk.LabelFrame(sidebar, text="1. Global Setup", padding="10")
        setup_box.pack(fill="x", pady=5)
        self.create_input(setup_box, "Race Length (min):", self.race_length_mins)
        self.create_input(setup_box, "Base Lap Time (s):", self.lap_time_secs)
        self.create_input(setup_box, "Energy Cap:", self.energy_cap)
        self.create_input(setup_box, "Energy/Lap:", self.energy_per_lap)
        self.create_input(setup_box, "Tire Life (laps):", self.tire_life_laps)
        self.create_input(setup_box, "Total Tires (All):", self.total_tires_avail)
        ttk.Button(setup_box, text="Generate Initial Plan", command=self.calculate).pack(fill="x", pady=5)

        live_box = ttk.LabelFrame(sidebar, text="2. Live Adjustments", padding="10")
        live_box.pack(fill="x", pady=5)
        self.create_input(live_box, "Laps Completed:", self.laps_completed)
        self.create_input(live_box, "Extra Pit Time (s):", self.extra_pit_time_secs)
        self.create_input(live_box, "Adj Lap Time (s):", self.new_lap_time_secs)
        self.create_input(live_box, "Adj Energy/Lap:", self.new_energy_per_lap)
        self.create_input(live_box, "Adj Tire Life:", self.new_tire_life)
        self.create_input(live_box, "Tires Rem. in Garage:", self.new_tires_remaining)

        tactical_box = ttk.LabelFrame(sidebar, text="3. Tactical Overrides", padding="10")
        tactical_box.pack(fill="x", pady=5)
        ttk.Checkbutton(tactical_box, text="Strict Tire Life (No 15% Margin)", variable=self.strict_tire_mode).pack(anchor="w")
        ttk.Label(tactical_box, text="Manual Time Rem. (min):").pack(anchor="w", pady=(5,0))
        ttk.Entry(tactical_box, textvariable=self.manual_rem_mins).pack(fill="x")
        ttk.Button(tactical_box, text="Apply & Recalculate", command=self.recalculate).pack(fill="x", pady=10)

        # Output Area
        self.out_frame = ttk.LabelFrame(self.root, text="Strategy Log", padding="10")
        self.out_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        self.out_frame.columnconfigure(0, weight=1)
        self.out_frame.rowconfigure(0, weight=1)

        self.output_text = tk.Text(self.out_frame, font=("Courier New", 11), wrap="none")
        self.output_text.tag_configure("warning", foreground="red", font=("Courier New", 11, "bold"))
        scroll_y = ttk.Scrollbar(self.out_frame, orient="vertical", command=self.output_text.yview)
        self.output_text.configure(yscrollcommand=scroll_y.set)
        self.output_text.grid(row=0, column=0, sticky="nsew")
        scroll_y.grid(row=0, column=1, sticky="ns")

    def create_input(self, parent, label, var):
        f = ttk.Frame(parent)
        f.pack(fill="x", pady=1)
        ttk.Label(f, text=label).pack(side="left")
        ttk.Entry(f, textvariable=var, width=10).pack(side="right")

    def calculate(self):
        self.output_text.delete(1.0, tk.END)
        self.output_text.insert(tk.END, ">>> INITIAL RACE STRATEGY [Inventory Gated]\n\n")
        self.run_simulation(self.race_length_mins.get(), self.lap_time_secs.get(), 
                           self.energy_per_lap.get(), self.tire_life_laps.get(), 
                           max(0, self.total_tires_avail.get() - 4), 0, False)

    def recalculate(self):
        manual = self.manual_rem_mins.get()
        rem_mins = float(manual) if manual.strip() else (self.race_length_mins.get() - ((self.laps_completed.get() * self.lap_time_secs.get()) + self.extra_pit_time_secs.get()) / 60)
        self.output_text.insert(tk.END, "\n" + "="*70 + "\n")
        self.output_text.insert(tk.END, f">>> RECALC: LAP {self.laps_completed.get()} | REM: {rem_mins:.2f}m\n\n")
        self.run_simulation(rem_mins, self.new_lap_time_secs.get(), 
                           self.new_energy_per_lap.get(), self.new_tire_life.get(), 
                           self.new_tires_remaining.get(), self.laps_completed.get(), True)
        self.output_text.see(tk.END)

    def run_simulation(self, rem_mins, lap_time, e_per_lap, t_life, tires_in_garage, start_lap, is_recalc):
        total_rem_secs = rem_mins * 60
        elapsed_secs = 0
        current_lap = start_lap
        tires_left = tires_in_garage 
        laps_on_current_set = 0
        stint_num = 1
        
        max_stint_laps = math.floor(self.energy_cap.get() / e_per_lap)
        
        # 1. DISTRIBUTION CALC
        estimated_stops = math.floor(total_rem_secs / (max_stint_laps * lap_time))
        available_swaps = tires_left // 4
        
        swap_needed = []
        if available_swaps >= estimated_stops:
            swap_needed = [True] * estimated_stops
        else:
            accumulator = 0.0
            ratio = available_swaps / estimated_stops if estimated_stops > 0 else 0
            for _ in range(estimated_stops):
                accumulator += ratio
                if accumulator >= 1.0:
                    swap_needed.append(True)
                    accumulator -= 1.0
                else:
                    swap_needed.append(False)
        
        self.output_text.insert(tk.END, f"Stint {stint_num:02d}: Driving {max_stint_laps} Laps\n")

        stop_idx = 0
        limit = t_life if self.strict_tire_mode.get() else (t_life * 1.15)

        while elapsed_secs < total_rem_secs:
            if elapsed_secs + (max_stint_laps * lap_time) >= total_rem_secs:
                laps_to_fin = math.ceil((total_rem_secs - elapsed_secs) / lap_time)
                self.output_text.insert(tk.END, f"FINISH - {laps_to_fin} laps to checkered flag.\n")
                self.output_text.insert(tk.END, f"         [Total Race Laps: {current_lap + laps_to_fin} | Tires Remaining: {tires_left}]\n")
                break

            elapsed_secs += (max_stint_laps * lap_time)
            current_lap += max_stint_laps
            laps_on_current_set += max_stint_laps
            
            # 2. DECISION LOGIC WITH HARD FLOOR
            should_swap = False
            if stop_idx < len(swap_needed):
                should_swap = swap_needed[stop_idx]
            
            # Safety Check Override
            if (laps_on_current_set + max_stint_laps) > limit:
                should_swap = True

            # THE HARD FLOOR: Final check against inventory
            if should_swap and tires_left < 4:
                should_swap = False

            if should_swap:
                action = "VE + TIRES"
                elapsed_secs += self.pit_tires_secs.get()
                tires_left -= 4
                laps_on_current_set = 0
            else:
                action = "VE ONLY"
                elapsed_secs += self.pit_energy_secs.get()

            # 3. WARNINGS & LOGGING
            danger = (laps_on_current_set + max_stint_laps) > limit
            time_str = f"+{int(elapsed_secs/3600):02d}h {int((elapsed_secs%3600)/60):02d}m"
            stint_num += 1
            
            line_text = f"LAP {current_lap:03d} - Stint {stint_num:02d}: {max_stint_laps} Laps | {action} | Tires in Garage: {tires_left}\n"
            
            if danger and not should_swap:
                self.output_text.insert(tk.END, f"  >> WARNING: TIRE WEAR EXCEEDS MARGIN ON NEXT STINT <<\n", "warning")
                self.output_text.insert(tk.END, line_text, "warning")
            else:
                self.output_text.insert(tk.END, line_text)
                
            self.output_text.insert(tk.END, f"          Pit Window: {time_str}\n\n")
            stop_idx += 1

if __name__ == "__main__":
    root = tk.Tk()
    app = RaceStrategyApp(root)
    root.mainloop()
