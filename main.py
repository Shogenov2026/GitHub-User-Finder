import tkinter as tk
from tkinter import messagebox, simpledialog
import requests
import json
import os

API_SEARCH_URL = "https://api.github.com/search/users"
FAV_FILE = "favorites.json"

def load_favorites():
    if os.path.exists(FAV_FILE):
        try:
            with open(FAV_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_favorites(favs):
    with open(FAV_FILE, "w", encoding="utf-8") as f:
        json.dump(favs, f, ensure_ascii=False, indent=2)

class GitHubUserFinder:
    def __init__(self, root):
        self.root = root
        self.root.title("GitHub User Finder")
        self.favorites = load_favorites()

        # Search frame
        frm = tk.Frame(root)
        frm.pack(padx=10, pady=8, fill="x")

        tk.Label(frm, text="Поиск пользователя GitHub:").pack(anchor="w")
        self.entry = tk.Entry(frm)
        self.entry.pack(fill="x", padx=0, pady=4)
        self.entry.bind("<Return>", lambda e: self.search())

        btn_frame = tk.Frame(frm)
        btn_frame.pack(fill="x")
        tk.Button(btn_frame, text="Поиск", command=self.search).pack(side="left")
        tk.Button(btn_frame, text="Показать избранное", command=self.show_favorites).pack(side="left", padx=6)

        # Results list
        tk.Label(root, text="Результаты:").pack(anchor="w", padx=10)
        self.results_list = tk.Listbox(root, height=10)
        self.results_list.pack(fill="both", expand=True, padx=10, pady=4)
        self.results_list.bind("<Double-Button-1>", lambda e: self.open_user_profile())

        # Bottom actions
        bottom = tk.Frame(root)
        bottom.pack(fill="x", padx=10, pady=6)
        tk.Button(bottom, text="Добавить в избранное", command=self.add_to_favorites).pack(side="left")
        tk.Button(bottom, text="Удалить из избранного", command=self.remove_from_favorites).pack(side="left", padx=6)
        tk.Button(bottom, text="Открыть профиль в браузере", command=self.open_user_profile).pack(side="right")

        self.last_results = []  # хранит данные последнего запроса

    def search(self):
        query = self.entry.get().strip()
        if not query:
            messagebox.showwarning("Ошибка ввода", "Поле поиска не должно быть пустым.")
            return
        params = {"q": query, "per_page": 30}
        try:
            resp = requests.get(API_SEARCH_URL, params=params, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            items = data.get("items", [])
            self.last_results = items
            self.results_list.delete(0, tk.END)
            if not items:
                self.results_list.insert(tk.END, "Ничего не найдено.")
                return
            for it in items:
                display = f"{it.get('login')} — {it.get('html_url')}"
                self.results_list.insert(tk.END, display)
        except requests.RequestException as e:
            messagebox.showerror("Ошибка сети", f"Не удалось выполнить запрос: {e}")

    def get_selected_user(self):
        sel = self.results_list.curselection()
        if not sel:
            messagebox.showinfo("Выбор", "Выберите пользователя в списке.")
            return None
        idx = sel[0]
        if idx >= len(self.last_results):
            messagebox.showinfo("Выбор", "Неверный выбор.")
            return None
        return self.last_results[idx]

    def add_to_favorites(self):
        user = self.get_selected_user()
        if not user:
            return
        login = user.get("login")
        if any(f.get("login") == login for f in self.favorites):
            messagebox.showinfo("Избранное", "Пользователь уже в избранном.")
            return
        # можно сохранять только нужные поля
        fav_item = {"login": login, "html_url": user.get("html_url"), "avatar_url": user.get("avatar_url")}
        self.favorites.append(fav_item)
        save_favorites(self.favorites)
        messagebox.showinfo("Избранное", f"{login} добавлен в избранное.")

    def remove_from_favorites(self):
        # диалог — удалить по логину
        login = simpledialog.askstring("Удалить", "Введите логин для удаления из избранного:")
        if not login:
            return
        before = len(self.favorites)
        self.favorites = [f for f in self.favorites if f.get("login") != login]
        if len(self.favorites) == before:
            messagebox.showinfo("Избранное", "Пользователь не найден в избранном.")
        else:
            save_favorites(self.favorites)
            messagebox.showinfo("Избранное", f"{login} удалён из избранного.")

    def show_favorites(self):
        favs = self.favorites
        win = tk.Toplevel(self.root)
        win.title("Избранные пользователи")
        lb = tk.Listbox(win, width=60)
        lb.pack(fill="both", expand=True, padx=8, pady=8)
        if not favs:
            lb.insert(tk.END, "Список избранного пуст.")
        else:
            for f in favs:
                lb.insert(tk.END, f"{f.get('login')} — {f.get('html_url')}")

    def open_user_profile(self):
        user = self.get_selected_user()
        if not user:
            return
        import webbrowser
        webbrowser.open(user.get("html_url"))

if __name__ == "__main__":
    root = tk.Tk()
    app = GitHubUserFinder(root)
    root.geometry("700x450")
    root.mainloop()
