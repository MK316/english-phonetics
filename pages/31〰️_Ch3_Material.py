import streamlit as st
import librosa
import librosa.display
import matplotlib.pyplot as plt
import numpy as np
import requests
import io

st.set_page_config(page_title="Spectrogram & Waveform Viewer", layout="centered")
st.title("🎧 Audio Visualization: Waveform + Spectrogram")
st.markdown("[I say tie](https://github.com/MK316/english-phonetics/blob/main/pages/audio/tie-dye-sty.mp3)")

# --- Audio file URL (raw GitHub link) ---
url = "https://raw.githubusercontent.com/MK316/english-phonetics/main/pages/audio/3words.mp3"

# --- Load audio from URL ---
@st.cache_data
def load_audio_from_url(url):
    response = requests.get(url)
    if response.status_code != 200:
        st.error("Audio could not be loaded.")
        return None, None
    audio_bytes = io.BytesIO(response.content)
    y, sr = librosa.load(audio_bytes, sr=None)
    return y, sr

y, sr = load_audio_from_url(url)

if y is not None:
    st.audio(url)

    # --- Plotting ---
    fig, ax = plt.subplots(2, 1, figsize=(10, 6), sharex=True)

    # Waveform
    librosa.display.waveshow(y, sr=sr, ax=ax[0], color='steelblue')
    ax[0].set(title='Waveform')
    ax[0].label_outer()

    # Spectrogram
    D = librosa.amplitude_to_db(np.abs(librosa.stft(y)), ref=np.max)
    img = librosa.display.specshow(D, sr=sr, x_axis='time', y_axis='log', ax=ax[1], cmap='magma')
    ax[1].set(title='Spectrogram (log scale)')
    fig.colorbar(img, ax=ax[1], format="%+2.0f dB")

    st.pyplot(fig)
else:
    st.warning("Unable to process the audio file.")
