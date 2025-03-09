## 1
- svedení se uvidí 
- vývoj na Raspberry Pi. 5 4GB
    - jaký ADC?
    - DMX interface? USB DMX interface? Využít GPIO?!
    - Jaký programovací jazyk využijem C nebo C++?

## 2
- externí školitel, možná i nějaká kačka, not sure for now.
- vedený do teoretickýho směru, prostě Filda stuff
- uživatelský profily, „světlo jako Korsakov“ atp.
- DMX převodník ENTTEX Open DMX, s tím že Python knihovny asi existují přes pyftdi
- ADC: zvuková karta
- https://github.com/maximecb/pyopendmx
- Dashboard!
- Založit GitHub, novej repo, otevřenej/zavřenej, helloworld: konzolová aplikace, vypíše „Hello World!“, 
- showcase dovedností - funkce, výpis do konzole, objekty? 

## 3
- Prozkoumat možnosti zpracování zvuku v Pythonu. PyAudio.
- Zapřemýšlet nad algoritmy rozpoznávání parametrů a vůbec si určit jaké parametry chceme sledovat. 
- algoritmus pro průměrnou hlasitost, program pro zobrazení průměrné hlasitosti/jiného parametru v reálném čase 

## 4
- Zapřemýšlet nad algoritmy rozpoznávání parametrů a vůbec si určit jaké parametry chceme sledovat. 
    - zatím RMS, supr
- Předělat na nekonečnou smyčku - vypočítávat RMS za celou vteřinu
- Beat detection?
- Frekvenční filtry, FFT

## 5
- Detekce BPM funguje s tleksáním, vyzkoušet hudbu
- Vymyslet nějaký robustní systém, navrhnout blokové schéma
- Nejvíc mě zajímají „reaktory“ - BPM reaktor, RMS reaktor, 
    - mně by se ještě líbil i Barevný reaktor = Spektrální reaktor
    - Josef: Autokorelační reaktor, detekce tonu kterej hraje.

## 6
- definovat si hodnoty vektoru popisujícího aktuální buffer 
    - downbeat: 0/1
    - RMS: float pásmový?
    - číslo noty tóniky 
    - …
- definovat převodní funkce jak se tenhleten vektor bude přetvářet v DMX hodnoty
- ideálně nějaký kódový prototyp


## 7 API
Work in porogress:
```Python
@dataclass
class BufferVector:
    beat: int # from 0..15, number of downbeat, light reaction on 1.
    base_tone: int # 0..6 
    sharp_diminished: Optional[bool]
    durr_moll: bool
    rms_mid: float
    rms_side: float
    # VL proposal:
    atmosphere: float # 0.. boring/balad/soft, 1..brutal goregrind metal - ???

```

### Python types
Python is not "type-safe", but you can sort of turn it on...
```Python
foo: int = 1
bar: float = 12.34
baz: str = "asdf" 
```
In addition, turn on type checking in VS Code, (python.analysis.type) (ctrl+,)


## 8
- Světla:
  1. rozchodit HW a odzkoušet na reálném světelném parku. (to je na dlouho, může počkat).
  1. ~~univerzáálně napsat nějakou knihovnu (?) nebo tak niečo, co by vytvořilo DMX loopback nebo virtuální BUS (?) a rozjet nějaký vizualizér.~~
- Determinace základního tónu.

### logger
```Python
import logging
import os

"""
CRITICAL: 50
ERROR: 40
WARNING: 30
INFO: 20
DEBUG: 10
NOTSET: 0
"""

logging.basicConfig(filename="test.log", 
    level=logging.DEBUG, 
    format="%(asctime)s:%(levelname)s:%(funcName)s:%(message)s")
logger = logging.getLogger(__name__)

def test():
    logger.debug("test function trace")
    if not os.path.isfile("soubor.txt"):
        logger.critical("soubor.txt not found")
        return
    with open("soubor.txt", "r") as file:
        print(file.read())
        logger.debug("soubr precten")

def info():
    logger.info("info function trace")

info()
test()
```

- maybe: Upravit konzolový výstup, ať se promazává po každém bufferu. <br> [Hint](https://stackoverflow.com/questions/52118317/how-to-clear-the-console-after-a-line-of-code)
- [Python Style Guide](https://peps.python.org/pep-0008/)


## 9
Yaml - configurační file (light_plot)
řešit typy světel resp. jejich argumenty pomocí data class?
Architekrura (multitasking) - Co běží v jakou chvíli 
Univerzální systém (převodní matice) Převod Audio do Light