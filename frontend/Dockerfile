# ==============================================================================
# Dockerfile para Frontend (React 19 + TypeScript + Vite)
# Panadería Santiago — SI-1
# ==============================================================================

FROM node:20-alpine

WORKDIR /app

# Copia los archivos de definición de paquetes primero
COPY package*.json ./

# Instala dependencias dentro del entorno Linux
RUN npm install

# Copia el resto del código del frontend
COPY . .

# Expone el puerto del servidor de desarrollo de Vite
EXPOSE 5173

# Arranca Vite en modo desarrollo escuchando en todas las interfaces de red
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
