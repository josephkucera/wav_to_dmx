Josef Diplomka
- svedení se uvidí 
- vývoj na Raspberry Pi. 5 4GB
    - jaký ADC?
    - DMX interface? USB DMX interface? Využít GPIO?!
    - Jaký programovací jazyk využijem C nebo C++?


- externí školitel, možná i nějaká kačka, not sure for now.
- vedený do teoretickýho směru, prostě Filda stuff
- uživatelský profily, „světlo jako Korsakov“ atp.
- DMX převodník ENTTEX Open DMX, s tím že Python knihovny asi existují přes pyftdi
- ADC: zvuková karta
- https://github.com/maximecb/pyopendmx
- Dashboard!
- Založit GitHub, novej repo, otevřenej/zavřenej, helloworld: konzolová aplikace, vypíše „Hello World!“, 
- showcase dovedností - funkce, výpis do konzole, objekty? 


- Prozkoumat možnosti zpracování zvuku v Pythonu. PyAudio.
- Zapřemýšlet nad algoritmy rozpoznávání parametrů a vůbec si určit jaké parametry chceme sledovat. 
- algoritmus pro průměrnou hlasitost, program pro zobrazení průměrné hlasitosti/jiného parametru v reálném čase 


- Zapřemýšlet nad algoritmy rozpoznávání parametrů a vůbec si určit jaké parametry chceme sledovat. 
    - zatím RMS, supr
- Předělat na nekonečnou smyčku - vypočítávat RMS za celou vteřinu
- Beat detection?
- Frekvenční filtry, FFT


- Detekce BPM funguje s tleksáním, vyzkoušet hudbu
- Vymyslet nějaký robustní systém, navrhnout blokové schéma
- Nejvíc mě zajímají „reaktory“ - BPM reaktor, RMS reaktor, 
    - mně by se ještě líbil i Barevný reaktor = Spektrální reaktor
    - Josef: Autokorelační reaktor, detekce tonu kterej hraje.


- definovat si hodnoty vektoru popisujícího aktuální buffer 
    - downbeat: 0/1
    - RMS: float pásmový?
    - číslo noty tóniky 
    - …
- definovat převodní funkce jak se tenhleten vektor bude přetvářet v DMX hodnoty
- ideálně nějaký kódový prototyp


- vektor:
    - [
        - 
