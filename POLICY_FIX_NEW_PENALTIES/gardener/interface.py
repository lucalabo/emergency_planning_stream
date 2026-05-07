import tkinter as tk


class Interface(tk.Frame):

    def __init__(self, instance):
        self.frame = tk.Tk()
        self.instance = instance

        # size for each cell in pixel
        self.size = 32

        # colors for the board
        self.color1 = "white"
        self.color2 = "grey"
        self.pieces = {}
        tk.Frame.__init__(self, self.frame)

        # Main layout: Canvas on left, Legend on right
        self.main_container = tk.Frame(self)
        self.main_container.pack(side="top", fill="both", expand=True)

        canvas_width = self.instance.size * self.size
        canvas_height = self.instance.size * self.size

        self.canvas = tk.Canvas(self.main_container, borderwidth=0, highlightthickness=0,
                                width=canvas_width, height=canvas_height,
                                background="bisque")
        self.canvas.pack(side="left", fill="both", expand=True, padx=2, pady=2)

        
        # Legend Frame
        self.legend_frame = tk.Frame(self.main_container, width=150, background="white", borderwidth=1, relief="sunken")
        self.legend_frame.pack(side="right", fill="y", padx=5, pady=2)
        
        tk.Label(self.legend_frame, text="LEGEND", font=("Arial", 12, "bold"), background="white").pack(pady=10)
        
        # Helper to add legend items
        def add_legend_item(img, text):
            item_frame = tk.Frame(self.legend_frame, background="white")
            item_frame.pack(fill="x", padx=10, pady=5)
            lbl_img = tk.Label(item_frame, image=img, background="white")
            lbl_img.pack(side="left")
            lbl_txt = tk.Label(item_frame, text=text, background="white", font=("Arial", 10))
            lbl_txt.pack(side="left", padx=5)

        # Initialize images
        self.player_image = tk.PhotoImage(data=IMAGEDATA_PLAYER)
        self.target_image = tk.PhotoImage(data=IMAGEDATA_TARGET)
        self.plant_image = tk.PhotoImage(data=IMAGEDATA_PLANT)
        self.frog_image = tk.PhotoImage(data=IMAGEDATA_FROG)
        self.mud_image = tk.PhotoImage(data=IMAGEDATA_MUD)
        self.water_image = tk.PhotoImage(data=IMAGEDATA_WATER)
        self.oil_image = tk.PhotoImage(data=IMAGEDATA_OIL)
        self.fire_image = tk.PhotoImage(data=IMAGEDATA_FIRE)

        # Populate Legend
        add_legend_item(self.player_image, "Player")
        add_legend_item(self.target_image, "Target")
        add_legend_item(self.plant_image, "Plant")
        add_legend_item(self.frog_image, "Frog")
        add_legend_item(self.mud_image, "Mud")
        add_legend_item(self.water_image, "Water")
        add_legend_item(self.oil_image, "Oil")
        add_legend_item(self.fire_image, "Fire")

        # this binding will cause a refresh if the user interactively
        # changes the window size
        self.canvas.bind("<Configure>", self.draw)

        self.pack(side="top", fill="both", expand=True, padx=4, pady=4)

        self.add_piece("player", self.player_image, self.instance.player)
        self.add_piece("target", self.target_image, self.instance.target)
        for count, plant in enumerate(self.instance.plants):
            self.add_piece("plant_" + str(count), self.plant_image, plant)
        if hasattr(self.instance, "frogs"):
            for count, frog in enumerate(self.instance.frogs):
                self.add_piece("frog_" + str(count), self.frog_image, frog)


        if hasattr(self.instance, "properties"):
            for loc, props in self.instance.properties.items():
                for i, prop in enumerate(props):
                    image = None
                    if prop == 'mud': image = self.mud_image
                    elif prop == 'water': image = self.water_image
                    elif prop == 'oil': image = self.oil_image
                    elif prop == 'fire': image = self.fire_image
                    
                    if image:
                        self.add_piece(f"prop_{loc}_{i}", image, loc)


    def add_piece(self, name, image, position):
        '''Add a piece to the playing board'''


        self.canvas.create_image(0, 0, image=image, tags=(name, "piece"),
                                 anchor="c")
        self.place_piece(name, position)

    def place_piece(self, name, position):
        '''Place a piece at the given row/column'''
        self.pieces[name] = position
        x0 = ((position[0] - 1) * self.size) + int(self.size / 2)
        y0 = ((position[1] - 1) * self.size) + int(self.size / 2)
        self.canvas.coords(name, x0, y0)

    def remove_pieces(self, name):
        remove_keys = []
        for key in self.pieces.keys():
            if key.startswith(name):
                remove_keys.append(key)
        for key in remove_keys:
            self.pieces.pop(key)
            self.canvas.delete(key)

    def draw(self, event):
        '''Redraw the board, possibly in response to window being resized'''
        xsize = int(event.width / self.instance.size)
        ysize = int(event.height / self.instance.size)
        self.size = min(xsize, ysize)
        self.canvas.delete("square")
        for row in range(self.instance.size):
            for col in range(self.instance.size):
                color = self.color1 if (col + 1,
                                        row + 1) not in self.instance.walls else \
                    self.color2
                x1 = (col * self.size)
                y1 = (row * self.size)
                x2 = x1 + self.size
                y2 = y1 + self.size
                self.canvas.create_rectangle(x1, y1, x2, y2, outline="black",
                                             fill=color, tags="square")
        for name in self.pieces:
            self.place_piece(name, self.pieces[name])
        self.canvas.tag_raise("piece")
        self.canvas.tag_lower("square")


IMAGEDATA_PLAYER = '''
    iVBORw0KGgoAAAANSUhEUgAAABgAAAAYCAYAAADgdz34AAAAAXNSR0IArs4c6QAAAERlWElmTU0
    AKgAAAAgAAYdpAAQAAAABAAAAGgAAAAAAA6ABAAMAAAABAAEAAKACAAQAAAABAAAAGKADAAQAAA
    ABAAAAGAAAAADiNXWtAAAAwklEQVRIDWNgGEnAE+jZx1AMYlMdgAz/D8UgNlGAiShVdFJEVhAxo
    jluBpCvB8QngfgGEN8B4hdA/BqIvwLxTyAGAXYg5gZiUSCWAGIVINYAYnMgvgTEGUCMFdwHisLC
    mVwaZAYcoPtADihjDcSGQKwJxMpALAPEvECMDXwGCj4B4rtAfB2IzwPxUSB+BMRggG4BTBydBvk
    GGyCon+apaNQCbPGCIjbyggiULAkmTeQwGnlBhOx7othDP4iI8uagVgQAnP4rQpmZ8u4AAAAASU
    VORK5CYII=
    '''

IMAGEDATA_PLANT = '''
    iVBORw0KGgoAAAANSUhEUgAAABgAAAAYCAYAAADgdz34AAAAAXNSR0IArs4c6QAAAERlWElmTU0
    AKgAAAAgAAYdpAAQAAAABAAAAGgAAAAAAA6ABAAMAAAABAAEAAKACAAQAAAABAAAAGKADAAQAAA
    ABAAAAGAAAAADiNXWtAAABOUlEQVRIDe2US0oDURBFoyC6BN2BQTQoRLPKoPE30J04EMkW1IkzI
    TjXgR8ieg6kQtHE0Hb3sC8cuvJevfq97nQ6rf45gR/85RXuYQhdaEyRID+nRD+BtSayvBHE4Fsw
    gAv4AtduYB1q6ZHTBjtMUfrYL7P107SuuQPH8ABRnOf/1IgdHTyUZRI7+YZtsJNzcHz6F2FpsXo
    sG+Qd9goujstAl3A3sz95noHjdKzu28lSXbGr4zPkJAbJlU74fQCh2HdcS7XB7hgMZieOyzuJCl
    3/gH3IshP3iuPNPnPbJNfguHLVYXtXWXbiuLwTL760rNLZP4FVR4Ij7JA+jss9L76yVjgZCTaxT
    WInkfgWu/Z3Egny0zH6ZtUOTox5B76Kvi3+hexCY4rKSwdcLe1Z0bFNUHFw7bE0gV8HXmSOKfy9
    ngAAAABJRU5ErkJggg==
    '''

IMAGEDATA_TARGET = '''
    iVBORw0KGgoAAAANSUhEUgAAABgAAAAYCAYAAADgdz34AAAAAXNSR0IArs4c6QAAAERlWElmTU0
    AKgAAAAgAAYdpAAQAAAABAAAAGgAAAAAAA6ABAAMAAAABAAEAAKACAAQAAAABAAAAGKADAAQAAA
    ABAAAAGAAAAADiNXWtAAABb0lEQVRIDd3UMU4DQQwF0ECkVHQ0CPpcgoKalgJqGgR34Ry5AiUHo
    KFGdCDlABSU8F8YS4ElG4SyTb70d2bsb3t2PLuj0bZjkhc8D2fhU/jWaM7GR/MvnCXqOfxYQxra
    P2Mc5W1YiR8yvw6n4V6jORtf6cSIXYtK/h7lZbjTE8FHQ6uQ2F54VUIBx025m/EmvAvnjeZsfEB
    bRVYel2bVmdsVHIX3YR3Dz5GPBsTwy/Fr490IAufq1e1OAraX8CI8aDRn46OhFVM9kauDWSwCNA
    8cQSXfX1i+P9iqCC2IFSNXB+4257R5nLO13cJpKCGaAx8NLYi1lqsDHxGnqwgaau1YoHbLZg581
    rQg1lquBeoW1Hrj43KB2sVhq/LYxpM2XmV8bTSH8pW2YivXl6o9Zxm93mBNHvyaTrL7QT80JzXo
    r0IBGPRnp8B4qYimb/x3rQg4ruqJQqtIs/IPGl8vNN7tcoV9/r5QNGfjo9lifALEXqkt2d8oHAA
    AAABJRU5ErkJggg==
    '''

IMAGEDATA_FROG = '''
    iVBORw0KGgoAAAANSUhEUgAAABwAAAAcCAYAAAByDd+UAAAACXBIWXMAAAsTAAALEwEAmpwYAAA
    CAUlEQVR4nO3VS4hOYRgH8N+4FzILcqeUMkWmSTRWLhtlSE0pKSVKuaRILqVsRJFLEVJ2mFiwkF
    sky9HkkizIdcFiMMY1IfTq+XKavr5zGHbfv9465znPef/vc/u/VFHFb/TCUmzEcP8Zo9GCeziHh
    2jGJNT8S6J+2IOv+BHEB9CJZ3iPJ1j5p8R9MBQj0DNsE3ETbajHU2zGKnxAA3pHpI9xqAjRdFzA
    x4ggre/owCfsQt/wnRYHSJGtzewxDJdxqRJRD+yNjVMT1EWUaY1BY0RbCTVYHnucRG0l59243Y1
    uG4DrkeamPOdZeB0N8LeYF3Xrr0AaUmSbdA87cLyI42K0R0q6gytYnee0MOamlPPTuIPtmJpTgj
    QyJdRGV0+uRNYQszMnYxuERTiBt7iG8WW6+QVmZmzrcDcvuiRH+yp8H4KjeIUJGXt9HGYUjmEc3
    mB+HmHSwLl5TjiMs5n3BbgVc9kZMra/wD6/5q6ty+nLoTnqWsIUvItU38epopqZ5OlIFPsGtnX5
    Pji6LnXwhpjRpojmM1qxJjJV0tpcJKE9Hyc+mCF6EPqZ1dLSc9LZGUF4JoZ9WVHCdOpvuIgtcaU
    sietmZ4zH+ujcNNRfsCL+HYnnIdztYU86OhsDK5E2xuYtQdwatXkUq6PLeomx8W9dxu9q3BAp4q
    1FI66iCuXwE3+he3aGwAhlAAAAAElFTkSuQmCC
    '''
IMAGEDATA_MUD = '''
    iVBORw0KGgoAAAANSUhEUgAAABgAAAAYCAYAAADgdz34AAADK0lEQVR42u1UO28kRRD+erp7pmdn
    5/btvQdnGZyAEA/pIiKcIn4BEgER/AgkpAsJSQnICAhBIiAgOoREgATRSQ7ubHzr0649t7vjeXZP
    dxGs92QOs2dEQnAllVrqrq7vq66uD3hhL+x/b+xfxq1XunBG/wXcu0Kct4ko27B/kVmkFAbS+SEA
    aKZNXSMBkAGwG6rb+ESd673gnU7o70mPvco5e4kxxABAhNo5TBrnHpzV7t6j0/wegMll5C4DkDe7
    /nu9WH2kJH9XSa8fSA7lCwhvFe6IUGqL2ljUxha1cb+muf76ICm/AbC4CMKeQfW3R+HHo1h9Fisx
    2uqGuNFvUacVUCeU4OcIRERZ1bBlodlsXuLxPMeyNPUi11/uH2d3ASTrnPxiJduD6IOtjvp83FXD
    t14e0Js7A9wetdlWN2QtJVjorzxSgoWSU2Vs2gpEfb0fCWud31i6E0qBJ5n+CUADgPEL7Hvbo9bd
    fuS/8fbu0G1vxfZgmp5Ml2UWCBEEknNHBDov/GB2lj6cZgd52SzG3TC6PWwHs0XJjXW3Sm1/rIyb
    AvCefrHY90ecY6elBI07IQ6maTLP9FFamKPDkzSxzkFwBu4xMIaVn/fDOodRN2TdKCDPo1Ecip11
    Q8W6GVbr1LkwqY1l81wTZx6Yx0Ag0OrnYLasaiLCsKOCm/0odoQdxoDtYRynpaG8NiBiWVXT6Rrg
    aQ8MkEdKbgnO9prG8l6spODw24Ho7N7oDIvamvtH88MkrZZtJdv9OJCDWKleFKh5VuO3B6f0eF56
    y0J/d5gUXwGo/wIAgOa5vh8p3taNu3NWaBkIEfViFYU+94rKNCfLauEcodcOOtYRn81L2j9e4veH
    CTt+UrBFYX74Y1Z9qq2drHOyS6a3vztufXIt9D9UPn+tFQgWBhxRIJHm2gBALw5kXhkUtUWhG1R1
    M8kq++1xcvbFmcb+ZXPwN4mIIvn6uC3fb/lyTwr2isfYkHsIV4MGYy0llmhSG/dzkprvT7PqFwD6
    KpP8rA712r4/vhayW57wVlLhbF1oejTPzQzAdMPdzWpKV5Bz9hxFZVeU7X+Ko+cx/hPEQYGlLPvt
    vwAAAABJRU5ErkJggg==
    '''

IMAGEDATA_WATER = '''
    iVBORw0KGgoAAAANSUhEUgAAABgAAAAYCAYAAADgdz34AAAEIElEQVR42rVVXWibZRR+zvt9+b4k
    TZMmTfqzUlfaum51VCtUURwUdTo2Rp1DQaEKIuxiE6wIQ5DFigjizS6dIHrhlRejXgwvZG6tU3Td
    cLPYbi2z/2nT5Eu6pvn7ft7jRTqQLelaf87Vy/u+nIfzPOecB9hWEECE/ysIgACglo5bC7G1b0wA
    WGvff9T90OF3ABYbd/9FOUwgArTQnh2vfTHRfHxoXdv51AsAgGhU/HtaSABAIHz4g7Mdn9zkPafn
    uPHVM39AC3WW9GD6pxQRokxgKQL7jg0Eug/2CU2X7JjS39XbWfvsiY/AHAApvBlVlQGiUcIgSc+D
    +/tqeo68rYUaBFtFgiNJ6LoMdB/oq+55fQAsBaKV9VAq8j7yNGu+BzrDhwY+8+3qaYZjSlJUQUIQ
    OzbU6pAQ3mB3IR674Xz7xgSiUYHhYS7XemV4JwZzoP7lT78MPn70CAmSVj4vpFmAIgjCpYM0jUnR
    KHXlu/H4N++9BCs9DpYEEG8OwEwgEqED774f3td/ilxuys1Nosq+beXTKWGk1lSXtxruukb4WnZL
    obpFcuTrs8a5D98EURpcaulKGggQMYAmX/sTryjeoDCu/YxHqlbTp4/33vj4xHNTHc3BXG4lhtWx
    yzCuXCB2LPa29RxUIl2Pgbmk3d9CvUtZAIOA7neRUFRj7FdoqVmr/63+5Yf3NmWlDRhaxPP5+emW
    leujWJuZhHHtEunBkFCqanUncS/fdwEMAgD0QA3nY9NYS66hqb6ag/UR2ywCgsHBYMCOdHaxJ9JA
    s98PIRObgX07AUXd4H5wK21aBLILMxC2CW7arf2SckeyRelazErvTwtmOF8wyROuQ92jT0JxuWCu
    JuAUi2VTqeXzF0BmjrRAA/w723FxXjbE122XIwnjBtcoRGDbhq+xGZ5wPTIzKUBVtjForBMYpOo6
    XF4fiNhq9dOPvS3qUK2HkkwCYGZFK72DGeDyg1a2ApgZG2BTWhZsyyRNEXZbkJJtITXhViyTQQAB
    7NhwzCIYsIlNcysADBBQWI1DmlNmbr0jF5uT6w1N3q/GzBfdLru4mHEahXRAmkY5Y0HmU0mQYy8V
    UvO3UEZlcQ9A9JQAUOBM7BwXMmyM/458YpkTjrt2NqvskFBIcWmw83kkx0bZymYIpvEDMovTG3Mr
    N99Fw8MACE76zxk11LrXctRdhXRC6r5qdukaICUK6SSWLo/I1M0JRWbjU07s6kmZS8aAqACG+X67
    6I75MvzhNnfL82eEv/kZtaoantoIhKIgnzJgZtbA2fgtc370mLPy2/mSLxBvcZtugBRzKXt1+ZLi
    9rkd06wtpFbcheQSW+vGCueWL9gLV086iesXKyXHFjz1zuIS8Eda9VB7GwtV5fX4vLUyOQUgv1ny
    bdgmVcC+vyf/BewL299kBereAAAAAElFTkSuQmCC
    '''

IMAGEDATA_OIL = '''
    iVBORw0KGgoAAAANSUhEUgAAABgAAAAYCAYAAADgdz34AAADBElEQVR42uWVy4scVRTGv3NudXVV
    V3XdnukZSI+ZCUQhEAxkEgIJ7rJJorgQXIzu3PoHOAuX48KNS7fuXAmCCNlJGEIe4oAuDEFxNJs4
    DzqT6UdVdffte48La6SJ053uwZ0XCopbdc7vq++cewr4Py0qLp4liGd4T5RS7zJ76zPGTi3irNZz
    v9Vq9T6AN/8ryJElQRhWvmw0lmVp6YzEcfITgJVpIGoK9c7z/A+1nvtIKc+JiCuV/MZwaBasHX4L
    QE4KYAAO8K5prT8vl8MIAIiImVmU4tf7/cGOiNs6qtEsACoCakmiv4jj5LwIxJg+W2uJWUmp5Csi
    udLv974DsDMOMgmgKpV4o1rVa8YY1+kccqnkp8b0XbvdKjGTC8Oo6px9zZjBbQBZEfdSwJGSpSSp
    fQaQbjZ3+cKFS4/X1ze+vnz56i+PHv34yv7+Tuz7vniefzbP0zsAto/7ikkd4IkInj9vUhhW8rW1
    D+6fO3d+7/r1G9u3br3zA7NCq3VAxgycUsqb+aAFQSB5nsGYAeJYD+fnF3tpmqpuN+VGYyXXui7W
    WmRZB5M6aSyg1+uh18sAACJUvXdvcxUQ/9mz/drW1sPVMIxJKQVrLVlrx9swqYdFhJTyEAQVefDg
    7tVmc7+eZWnlyZM/loMgFN8PKM/TE88iKtoeREye5w1WV698tbx85g4zg4hAxKN5aFbAEMAAEIiI
    WOvU3t7uUqfTXhARiPxjvQPQG6kDvahy3CErAfgGoJunTq1IFGlmJvydXGDMwD19+jtZa7YBvA2g
    BWB3mjaVYt8A2ASEut1DEAHOORERYVZI0zasNQSgValUN2q1hfvlcvQpgHhU/MtGxZ8A3jJmUCfi
    YbkcMABkWVsODnbJOXfIrPbq9cYNrRdqztk38ry7Oe7QHQcBgPcA5ACkXA4lDCMhYimCPwG8a0ky
    /3hx8fQwivRtAKcn2D8W8j6A74tiDgH8CuBjAFHx/FUANwHMjUswzUoAXAQQAPi5sG9krP/L3hP9
    Nl/co5F7dZzgvwCOmzWZ2MZdxwAAAABJRU5ErkJggg==
    '''

IMAGEDATA_FIRE = '''
    iVBORw0KGgoAAAANSUhEUgAAABgAAAAYCAYAAADgdz34AAADl0lEQVR42q1Wz28bRRT+3syu116v
    7fxoit04CShV09a5ICCFqkJFqFIOCIljuPZCw49zLygJnMqBC/wHHEFwABVVSKglURvUtEWiQUpo
    2kJFaF0njX/E9u7OvOFgV00Tu02RnzR6o9XO981+b795AzxDUHM8Sp0L2gIsO01Cpgn29p7IRxP7
    op8DSDTRRcfAT/Q6kz8c31OeH0+bk0PulwA8sQsS+RRwEGDGe53JD3KJM8eyrrfXs3jQtY6YgLuu
    FsNfBOCbJ8gln6C5mQYwkY1Nvj+aOnM063qBNhyyQdqzMeRZY02SWQL8djVpSWAAmgbExEDsvVO5
    1GevZKKe7zPTkGPMczbrfEhpz8ZQ3BoTISeuFMO5diSt9BMEmHQEB98d9k6/nHa8qs+MHou8N7op
    daJHcNrmesDI7XXwzgveqWMpOW4ATO2GYGqqkY/2xQ4NJu1MoIyhqKD4610mNhAV0Z6IjB/vAnuC
    Q2XM/h5bHk5FXgSAaQPzVILpZh5J2iPdjrA1APdIktzRuIA2gDJI7I/L6KsJVgI6GRHo9+wRABEp
    YLbLtJ2A5CdgAGIwZR1KWgJISBM97Dbt1RwC5ByIU+AK7UpCf8IaBtBrTAu9dxS48VJvJiZHLEGN
    ioiHm9IA1CMfi8Yk48rssGU936oObU3CO3bDgEgwy14NmMdQ2LQ3k2gBTAAKy8VgoaoYMIBhDVh9
    Cvsm72Hg9L+IHqyzVgDIKDa4UQyWVpRaIgJm8HihxQ4LEAiAuXLXn1vd1BoVpvKfFQVvrILEa5vC
    zdXQ/Wap/JcKZUWJQp3xx1o4D2CdubF2V3/R7Fr9t9WauuOwodrlMpdXEUCCIDSV81a9ulBhlyly
    uxQE14v+PABM0y58MAMYQcDdACsrG+HvigC5wVbp3PmIKt6SrIpi/aezESdfdSAIN4vh35eK+mpz
    7Y6wWp0UmkFE8Bcf+Bfv1/RbfTGbStcX44UfPyXZnWR9+WI0GbFkyWezvBFeA3BHEMC7MdrWT529
    58//+k+1ptlQXFiy8vM1u/D9eSsZsqOYaGG1Rovr9UsAgo8NxHb92x52F5r5fmjy1apWOtQvZRNW
    LAlJMV9IXxnr3EqFv721+dVcIfyiBpQu/I9+AALCGzU9e7uoljdrejQTk2mwkd8slfNf39ycOfsg
    nKkBax3paDaQO9kf/e7DQXf+gCPH0ckLwJaO1QUgs+VZR28X4iGieQbg/wDzLIMuSQhtGQAAAABJ
    RU5ErkJggg==
    '''
