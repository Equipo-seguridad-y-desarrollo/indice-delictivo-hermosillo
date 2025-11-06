# 🔐 IMPORTANTE: Configuración de Seguridad

## ⚠️ NUNCA subas el archivo `.env` a GitHub

El archivo `.env` contiene información sensible (API keys) y está protegido por `.gitignore`.

## 📋 Instrucciones para otros usuarios del proyecto

Si clonas este repositorio, necesitarás crear tu propio archivo `.env`:

1. **Crea un archivo `.env` en la raíz del proyecto**
   ```bash
   touch .env
   ```

2. **Agrega tus credenciales**
   ```env
   # Google Maps API Key
   GOOGLE_MAPS_API_KEY=tu_api_key_aqui
   ```

3. **Obtén tu API Key de Google Maps**
   - Ve a [Google Cloud Console](https://console.cloud.google.com/)
   - Habilita la API de Geocoding
   - Crea credenciales (API Key)
   - Copia tu API key al archivo `.env`

## 🛡️ Buenas prácticas de seguridad implementadas

✅ API Key almacenada en variable de entorno  
✅ Archivo `.env` incluido en `.gitignore`  
✅ Librería `python-dotenv` para manejo seguro de variables  
✅ Validación de API key antes de ejecutar el script  

## 📝 Scripts que requieren configuración

- `obtener_coordenadas_colonias.py` - Requiere `GOOGLE_MAPS_API_KEY`

## 🚨 Si accidentalmente expusiste tu API Key

1. **Revoca la key inmediatamente** en Google Cloud Console
2. **Genera una nueva API key**
3. **Actualiza tu archivo `.env`**
4. **Si subiste a GitHub**, considera el historial contaminado y posiblemente necesites crear un nuevo repositorio

## 💰 Control de costos

- Google Maps Geocoding: $5 USD por 1,000 peticiones
- Incluye $200 USD de crédito gratis mensual
- El script usa `delay=0.2s` entre peticiones para evitar exceder límites
- Monitorea tu uso en [Google Cloud Console](https://console.cloud.google.com/)
