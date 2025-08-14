import tkinter as tk
from tkinter import ttk, messagebox, simpledialog

# ---- Currency rates (BASE = USD). Update via "Manage Rates" in the UI. ----
CURRENCY_RATES = {
    "USD": 1.0,
    "INR": 83.2,   # placeholder
    "EUR": 0.92,   # placeholder
    "GBP": 0.78,   # placeholder
    "JPY": 141.5,  # placeholder
    "AED": 3.67,   # pegged approx
}

# ------------------ Standard Calculator Logic ------------------ #
class StandardCalculator(ttk.Frame):
    def __init__(self, master):
        super().__init__(master, padding=10)
        self.expression = ""
        self.input_var = tk.StringVar()

        # Display
        entry = ttk.Entry(self, textvariable=self.input_var, font=("Arial", 20), justify="right")
        entry.grid(row=0, column=0, columnspan=4, sticky="nsew", ipady=8, pady=(0,8))
        entry.bind("<Key>", self._key_handler)
        entry.focus()

        # Buttons layout
        buttons = [
            ["CE", "C", "(", ")"],
            ["7", "8", "9", "/"],
            ["4", "5", "6", "*"],
            ["1", "2", "3", "-"],
            ["0", ".", "%", "+"],
            ["√", "^", "=", ""],
        ]

        for r, row in enumerate(buttons, start=1):
            for c, label in enumerate(row):
                if not label:  # empty spacer
                    continue
                b = ttk.Button(self, text=label, command=lambda t=label: self.on_click(t))
                b.grid(row=r, column=c, sticky="nsew", padx=3, pady=3, ipadx=4, ipady=8)

        # Grid weights
        for i in range(4):
            self.columnconfigure(i, weight=1)
        for i in range(len(buttons)+1):
            self.rowconfigure(i, weight=1)

    def _sanitize(self, s: str) -> str:
        # Replace user-friendly ops with Python equivalents
        s = s.replace("√", "sqrt(")       # add opening paren; user can close or we will
        s = s.replace("^", "**")
        # Percent: treat 'x%' as x/100
        # cheap transform: replace occurrences of number% with (number/100)
        import re
        s = re.sub(r'(?<!\w)(\d+(\.\d+)?)\%', r'(\1/100)', s)
        # If sqrt( not closed, add closing ')'
        opens = s.count("sqrt(")
        closes = s.count(")")
        # try not to over-close; only close if needed at end
        if opens > s.count("sqrt(") - (closes - s.count("(")):
            pass
        return s

    def evaluate(self):
        expr = self.input_var.get().strip()
        if not expr:
            return
        expr = self._sanitize(expr)
        try:
            # Safe eval: allow only math ops
            import math
            allowed = {"__builtins__": {}}
            safe_funcs = {k: getattr(math, k) for k in dir(math) if not k.startswith("_")}
            allowed.update(safe_funcs)
            result = eval(expr, allowed, {})
            self.input_var.set(str(result))
            self.expression = str(result)
        except Exception:
            self.input_var.set("Error")
            self.expression = ""

    def on_click(self, t: str):
        if t == "=":
            self.evaluate()
        elif t == "C":  # clear all
            self.expression = ""
            self.input_var.set("")
        elif t == "CE":  # clear last char
            cur = self.input_var.get()
            self.input_var.set(cur[:-1])
            self.expression = self.input_var.get()
        elif t == "√":
            # insert sqrt(
            self.expression = self.input_var.get() + "√"
            self.input_var.set(self.expression)
        elif t == "^":
            self.expression = self.input_var.get() + "^"
            self.input_var.set(self.expression)
        else:
            self.expression = self.input_var.get() + t
            self.input_var.set(self.expression)

    def _key_handler(self, event):
        # Enter to evaluate
        if event.keysym == "Return":
            self.evaluate()
            return "break"
        # Escape clears
        if event.keysym == "Escape":
            self.input_var.set("")
            self.expression = ""
            return "break"
        # Let normal typing happen
        return None

# ------------------ Currency Converter Logic ------------------ #
class CurrencyConverter(ttk.Frame):
    def __init__(self, master):
        super().__init__(master, padding=10)

        # Title row
        title = ttk.Label(self, text="Currency Converter (Base = USD, editable rates)", font=("Arial", 12))
        title.grid(row=0, column=0, columnspan=4, sticky="w", pady=(0,10))

        # Amount
        ttk.Label(self, text="Amount:").grid(row=1, column=0, sticky="e")
        self.amount_var = tk.StringVar()
        ttk.Entry(self, textvariable=self.amount_var).grid(row=1, column=1, sticky="ew", padx=(6,12))

        # From / To
        self.currencies = sorted(CURRENCY_RATES.keys())
        ttk.Label(self, text="From:").grid(row=2, column=0, sticky="e")
        self.from_var = tk.StringVar(value="USD")
        self.from_combo = ttk.Combobox(self, textvariable=self.from_var, values=self.currencies, state="readonly")
        self.from_combo.grid(row=2, column=1, sticky="ew", padx=(6,12))

        ttk.Label(self, text="To:").grid(row=2, column=2, sticky="e")
        self.to_var = tk.StringVar(value="INR")
        self.to_combo = ttk.Combobox(self, textvariable=self.to_var, values=self.currencies, state="readonly")
        self.to_combo.grid(row=2, column=3, sticky="ew", padx=(6,0))

        # Buttons
        convert_btn = ttk.Button(self, text="Convert", command=self.convert)
        swap_btn = ttk.Button(self, text="Swap", command=self.swap)
        manage_btn = ttk.Button(self, text="Manage Rates", command=self.manage_rates)

        convert_btn.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(8,8), padx=(0,6))
        swap_btn.grid(row=3, column=2, sticky="ew", pady=(8,8), padx=(6,6))
        manage_btn.grid(row=3, column=3, sticky="ew", pady=(8,8), padx=(6,0))

        # Result
        self.result_var = tk.StringVar(value="Result will appear here")
        result_lbl = ttk.Label(self, textvariable=self.result_var, font=("Arial", 14))
        result_lbl.grid(row=4, column=0, columnspan=4, sticky="ew", pady=(6,0))

        # Table of current rates
        ttk.Label(self, text="Rates (per 1 USD):").grid(row=5, column=0, columnspan=4, sticky="w", pady=(12, 4))
        self.rates_tree = ttk.Treeview(self, columns=("cur","rate"), show="headings", height=6)
        self.rates_tree.heading("cur", text="Currency")
        self.rates_tree.heading("rate", text="Rate per USD")
        self.rates_tree.grid(row=6, column=0, columnspan=4, sticky="nsew")
        self._refresh_rates_table()

        # Grid weights
        for i in range(4):
            self.columnconfigure(i, weight=1)
        self.rowconfigure(6, weight=1)

    def _refresh_rates_table(self):
        for i in self.rates_tree.get_children():
            self.rates_tree.delete(i)
        for cur in sorted(CURRENCY_RATES.keys()):
            self.rates_tree.insert("", "end", values=(cur, CURRENCY_RATES[cur]))

    def swap(self):
        f, t = self.from_var.get(), self.to_var.get()
        self.from_var.set(t)
        self.to_var.set(f)

    def convert(self):
        try:
            amt = float(self.amount_var.get())
        except ValueError:
            messagebox.showerror("Invalid amount", "Please enter a valid number for amount.")
            return

        from_cur = self.from_var.get()
        to_cur = self.to_var.get()
        if from_cur not in CURRENCY_RATES or to_cur not in CURRENCY_RATES:
            messagebox.showerror("Unknown currency", "Selected currency not in rate table.")
            return

        # Convert: amt_from -> USD -> target
        usd = amt / CURRENCY_RATES[from_cur]
        out = usd * CURRENCY_RATES[to_cur]
        self.result_var.set(f"{amt:.4f} {from_cur} = {out:.4f} {to_cur}")

    def manage_rates(self):
        # Simple dialog loop to add/update a rate
        cur_list = ", ".join(sorted(CURRENCY_RATES.keys()))
        cur = simpledialog.askstring("Edit Rate", f"Enter currency code to edit/add (e.g., USD, INR).\nCurrently: {cur_list}")
        if not cur:
            return
        cur = cur.strip().upper()
        rate_str = simpledialog.askstring("Edit Rate", f"Enter rate for 1 USD in {cur} (e.g., 83.20 for INR):")
        if not rate_str:
            return
        try:
            rate = float(rate_str)
            if rate <= 0:
                raise ValueError()
        except Exception:
            messagebox.showerror("Invalid rate", "Please enter a positive number.")
            return

        CURRENCY_RATES[cur] = rate
        if cur not in self.currencies:
            self.currencies.append(cur)
            self.currencies.sort()
            self.from_combo["values"] = self.currencies
            self.to_combo["values"] = self.currencies
        self._refresh_rates_table()
        messagebox.showinfo("Saved", f"Rate updated: 1 USD = {rate} {cur}")

# ------------------ Main App ------------------ #
class AdvancedCalculatorApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Advanced Calculator")
        self.geometry("440x520")
        self.minsize(420, 480)

        # Modern ttk theme tweaks
        style = ttk.Style(self)
        # Use default theme with slight padding
        style.configure("TButton", padding=6)
        style.configure("TEntry", padding=4)

        notebook = ttk.Notebook(self)
        notebook.pack(expand=True, fill="both")

        self.std_calc = StandardCalculator(notebook)
        self.curr_conv = CurrencyConverter(notebook)

        notebook.add(self.std_calc, text="Calculator")
        notebook.add(self.curr_conv, text="Currency")

if __name__ == "__main__":
    app = AdvancedCalculatorApp()
    app.mainloop()
