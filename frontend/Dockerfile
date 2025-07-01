# Use the official lightweight Nginx image
FROM nginx:alpine

# Copy static files to Nginx's default serving directory
COPY . /usr/share/nginx/html

# Expose port 80 (Nginx default)
EXPOSE 80

# Start Nginx
CMD ["nginx", "-g", "daemon off;"]