from bs4 import BeautifulSoup
import requests
import csv
import pandas as pd
import re
from tkinter import *
from tkinter import ttk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg)

# Duomenu nuskaitymas is pirmu 10 cvmarket.lt puslapiu
r = requests
bs = BeautifulSoup
url = 'https://www.cvmarket.lt/joboffers.php?_track=index_click_job_search&op=search&search_location=landingpage&ga_track=homepage&search%5Bkeyword%5D=&search%5Bexpires_days%5D=&search%5Bjob_lang%5D=&search%5Bsalary%5D=&search%5Bjob_salary%5D=3&mobile_search%5Bkeyword%5D=&tmp_city=&tmp_cat=&tmp_category=&start='

with open("Darbo skelbimai.csv", "w", encoding="UTF-8", newline='') as failas:
    csv_writer = csv.writer(failas)
    csv_writer.writerow(['Pareigos', 'Miestas', 'Darbdavys', 'Atlyginimas_skelbime', 'Tipas', 'Atlyginimas_i_rankas'])

    for p in range(0, 300, 30):
        source = r.get(url + str(p)).text
        soup = bs(source, 'html.parser')
        # print(soup)
        block = soup.find_all('tr', class_='f_job_row2')
        # print(block.prettify())

        for a in block:
            try:
                pareigos = a.find('a', class_='f_job_title main_job_link limited-lines').text.strip()
                # print(pareigos)
            except:
                pareigos = 'N/A'
            try:
                imone = a.find('span', class_='f_job_company').text.strip()
                # print(imone)
            except:
                imone = 'N/A'
            try:
                atlyginimas = a.find('span', class_='f_job_salary').text.strip()
                # nuvalomi simboliai
                atlyginimas = re.sub(' €/mėn.', '', atlyginimas)
                atlyginimas = re.sub(' €/val.', '', atlyginimas)
                atlyginimas = re.sub('Nuo ', '', atlyginimas)
                atlyginimas = re.sub('Iki ', '', atlyginimas)
                # jei atlyginimas nurodomas intervalu, tai kaip siūlomas atlyginimas imama žemiausia nurodyto intervalo žyma
                if len(atlyginimas) > 4:
                    atlyginimas = atlyginimas.split(' - ')[0]
                # print(atlyginimas)
            except:
                atlyginimas = 'N/A'
            try:
                atlyginimo_tipas = a.find('span', class_='salary-type').text.strip()
                # print(atlyginimo_tipas)
            except:
                atlyginimo_tipas = 'N/A'
            try:
                miestas = a.find('div', class_='f_job_city').text.strip()
                # print(miestas)
            except:
                miestas = 'N/A'

            # atlyginimas neatskaicius mokesciu perskaiciuojamas i atlyginima i rankas
            rankas = 0
            if atlyginimo_tipas == 'Neatskaičius mokesčių':
                if float(atlyginimas) < 730 or float(atlyginimas) == 730:
                    npd = 460
                    gpm = (float(atlyginimas) - npd) * 0.2
                    sodra = float(atlyginimas) * 0.195
                    rankas = round(float(atlyginimas) - gpm - sodra, 2)
                elif float(atlyginimas) > 730 and float(atlyginimas) < 1678:
                    npd = 460 - 0.26 * (float(atlyginimas) - 730)
                    gpm = (float(atlyginimas) - npd) * 0.2
                    sodra = float(atlyginimas) * 0.195
                    rankas = round(float(atlyginimas) - gpm - sodra, 2)
                else:
                    npd = 400 - 0.18 * (float(atlyginimas) - 642)
                    if npd > 0:
                        npd = npd
                    else:
                        npd = 0
                    gpm = (float(atlyginimas) - npd) * 0.2
                    sodra = float(atlyginimas) * 0.195
                    rankas = round(float(atlyginimas) - gpm - sodra, 2)
            else:
                rankas = atlyginimas

            csv_writer.writerow([pareigos, miestas, imone, atlyginimas, atlyginimo_tipas, rankas])

#darbo skelbimu data Frame
df = pd.read_csv('Darbo skelbimai.csv', delimiter=',')


# grafinė sąsaja
class app(Tk):
    def __init__(self):
        Tk.__init__(self)

        # sąsajos pavadinimas ir ikona
        self.iconbitmap('job.ico')
        self.title('Darbo paieška')

        # Combobox nustatymas miesto filtravimui
        self.label = ttk.Label(text='Pasirinkite miestą, kuriame norite įsidarbinti: ')
        self.label.pack(fill=X, padx=5, pady=5)

        self.Combo = ttk.Combobox(self, values=[''] + list(df["Miestas"].unique()), state="readonly")
        self.Combo.pack(fill=X, padx=5, pady=5)
        self.Combo.bind("<<ComboboxSelected>>", self.select_city)

        # pasirinkto miesto darbo skelbimų pateikimas
        self.tree = ttk.Treeview(self)
        columns = list(df.columns)
        self.tree["columns"] = columns
        self.tree.pack(expand=TRUE, fill=BOTH)

        for i in columns:
            self.tree.column(i, anchor="w")
            self.tree.heading(i, text=i, anchor="w")

        for index, row in df.iterrows():
            self.tree.insert("", "end", text=index, values=list(row))

        # mygtukas papildoma informacija apie pasirinkto miesto darbo skelbinus grafiškai
        self.button = ttk.Button(self, text="Informacija apie darbdavius pasirinktame mieste", command=self.info)
        self.button.pack(fill=X)

        self.fig = Figure(figsize=(13, 4), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        graph_widget = self.canvas.get_tk_widget()
        graph_widget.pack()

    # darbo skelbimų filtravimas pagal pasirinktą miestą
    def select_city(self, event=None):
        self.tree.delete(*self.tree.get_children())
        if self.Combo.get() == '':
            for index, row in df.iterrows():
                self.tree.insert("", "end", text=index, values=list(row))
        else:
            for index, row in df.loc[df["Miestas"].eq(self.Combo.get())].iterrows():
                self.tree.insert("", "end", text=index, values=list(row))

    # grafikų braižymas pagal pasirinktą miestą
    def info(self):
        dfm = df.loc[df["Miestas"].eq(self.Combo.get())]
        df_group_mean = dfm.groupby('Darbdavys')['Atlyginimas_i_rankas'].mean()

        dfm = df.loc[df["Miestas"].eq(self.Combo.get())]
        df_group_count = dfm.groupby('Darbdavys')['Pareigos'].count()

        self.fig.clear()
        a1 = self.fig.add_subplot(121, title="Vidutinis siūlomas atlyginimas įmonėje")
        a1.barh(df_group_mean.index, df_group_mean.values, color='red')
        a1.set_ylabel('Imone', fontsize=9)
        a1.set_xlabel('Vidutinis atlyginimas (Į rankas)', fontsize=9)
        a1.grid(axis='y')
        a2 = self.fig.add_subplot(122, title='Ieškomas darbuotojų skaičius')
        a2.barh(df_group_count.index, df_group_count.values, color='red')
        a2.get_yaxis().set_visible(False)
        a2.set_xlabel('Darbo skelbimų kiekis', fontsize=9)
        a2.grid(axis='y')
        self.fig.subplots_adjust(wspace=0, hspace=0)
        self.canvas.draw_idle()


langas = app()
langas.mainloop()