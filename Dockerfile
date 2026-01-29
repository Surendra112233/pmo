# using node version 22
FROM node:22.13.1-alpine
# workinhg directory in the container
WORKDIR /app
#copying package files into the container
COPY package*.json ./
#to install the dependencies
RUN npm install --legacy-peer-deps
#copying the entire project directory into the container
COPY . .
#setting up environment variable port
ENV PORT=8301
#build the angular app - for build and run locally first
RUN npm run build
#installing simple server to serve teh built app
RUN npm install -g serve
#expose the port number for outside
EXPOSE 8301
#command to serve the built Angular app
CMD ["serve", "-s", "dist/angularmaterial", "-l", "8301"]
