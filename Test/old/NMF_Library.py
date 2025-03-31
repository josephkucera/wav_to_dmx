import numpy as np
import librosa
import os
from sklearn.decomposition import NMF

def train_and_save_basis_from_folder(folder, output_file, sr=22050, n_fft=2048, hop_length=512, n_components=5):
    """ Trénuje spektrální vzory pro jeden nástroj na základě všech souborů ve složce """
    all_spectrograms = []

    # 1. Načtení všech .wav souborů ve složce
    audio_files = [os.path.join(folder, f) for f in os.listdir(folder) if f.endswith(".wav")]
    if not audio_files:
        print(f"⚠️ Ve složce {folder} nejsou žádné .wav soubory!")
        return

    calc = 0
    for file in audio_files:
        y, _ = librosa.load(file, sr=sr)
        S = np.abs(librosa.stft(y, n_fft=n_fft, hop_length=hop_length))
        all_spectrograms.append(S)
        calc = calc +1
        print(calc)

    # 2. Spojení spektrogramů do jedné matice
    combined_S = np.concatenate(all_spectrograms, axis=1)
    print("spojit")

    # 3. Trénování NMF
    nmf = NMF(n_components=n_components, solver='mu', beta_loss='itakura-saito')
    W = nmf.fit_transform(combined_S.T)
    print("nmf done")

    # 4. Uložení naučených spektrálních vzorů
    np.save(output_file, nmf.components_)
    print(f"✅ Uloženo: {output_file}")
    
    
def load_basis_library(folder):
    """ Načte všechny uložené vzory z .npy souborů ve složce a spojí je do jedné databáze """
    basis_library = []

    for file in os.listdir(folder):
        if file.endswith(".npy"):
            basis = np.load(os.path.join(folder, file))
            basis_library.append(basis)

    if not basis_library:
        raise ValueError("⚠️ Nebyla nalezena žádná uložená databáze!")

    return np.concatenate(basis_library, axis=0)  # Spojení všech vzorů do jedné matice

# Příklad použití – načteme všechny naučené nástroje:
basis_library = load_basis_library("datasets")  # Složka, kde jsou .npy soubory
np.save("full_basis_library.npy", basis_library)  # Uložíme kompletní databázi

# 🔥 Příklad použití – natrénujeme a uložíme každý nástroj:
# train_and_save_basis_from_folder("test/database/", "piano_basis.npy", n_components=5)
train_and_save_basis_from_folder("test/database/el_guit", "guitar_basis.npy", n_components=4)
# train_and_save_basis_from_folder("test/database/", "drums_basis.npy", n_components=5)
# train_and_save_basis_from_folder("test/database/", "bass_basis.npy", n_components=5)
