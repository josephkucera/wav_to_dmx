class VectorClass:
    def __init__(self, audio_obj,light_obj, beat: int = 0, base_tone: int= 0, sharp_diminished: bool= 0,
                 durr_moll: bool= 0, rms_mid: float= 0, rms_side: float= 0, atmosphere: float= 0, bpm: int= 0):
        self.audio = audio_obj
        self.light_obj = light_obj
        self.beat = 0
        self.bpm = 0
        self.rms = 0
        self.bpm = 0
        # self.base_tone = base_tone
        # self.sharp_diminished = sharp_diminished
        # self.durr_moll = durr_moll
        # self.rms_mid = rms_mid
        # self.rms_side = rms_side
        # self.atmosphere = atmosphere
        
    def GetBeat(self):
        """
        Aktualizuje hodnotu beat podle hodnoty peak_boll z AudioAnalysis.
        """
        self.beat = self.audio.peak_boll  # Přímý přístup k hodnotě z AudioAnalysis
        return self.beat
  
        
    def GetBpm(self):
        """
        Aktualizuje hodnotu BPM podle hodnoty z AudioAnalysis
        """
        self.bpm = self.audio.bpm # Přímý přístup k hodnotě z AudioAnalysis
        return self.bpm
    
    def GetRms(self):
        """
        Aktualizuje hodnotu rms podle hodnoty z AudioAnalysis
        """
        self.rms = self.audio.rms
        self.db = self.audio.db
        return self.db,self.rms

    
    def GetInfo(self):
        """
        Přístup ke všem hodnotám 
        """
        beat = self.GetBeat()
        bpm = self.GetBpm()
        # rms, db = self.GetRms()
        # print(f" audio boll má hodnotu {self.beat} a bpm je aktualne {self.bpm}")
        # print(f"\n Střední hodnota je {self.rms} což odpovídá {self.db}")
    
    def UpdateLights(self):
        """
        Aktualizuje světla na základě hodnoty beatu nebo jiných parametrů.
        """
        beat = self.GetBeat()
        bpm = self.GetBpm()
        
        tab_x = {1: "red"}
        
        if beat > 0:
            self.light_obj.beat_effect()
            print("bum bum beat")
            
        if 0 < bpm <= 50:
            self.light_obj.set_lights_blue()
        elif 50 < bpm <= 100:
            self.light_obj.set_lights_red()
        else:
            self.light_obj.set_lights_green()
