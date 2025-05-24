# Gallery Images for Umbrel App

This directory should contain screenshots of the MongoDB MCP Server for the Umbrel App Store.

## Required Images:

- **1.jpg** - Main dashboard view showing active connections and MCP tools
- **2.jpg** - Web interface displaying real-time MCP activities and queries  
- **3.jpg** - Example of MongoDB schema analysis and data exploration

## Specifications:

- **Format**: JPG
- **Size**: 1920x1080 (Full HD) recommended
- **Content**: Clean, professional screenshots showing actual functionality
- **Quality**: High quality, sharp images with good contrast

## How to Create:

1. Start the MongoDB MCP Server in Umbrel
2. Access the web interface at `http://your-umbrel-ip:8080`
3. Connect to a MongoDB database through Cursor IDE
4. Take screenshots of:
   - Dashboard with active connections
   - Real-time activity monitoring
   - Example queries and results

## Temporary Placeholders:

For development purposes, create placeholder images:
```bash
# Create placeholder images (replace with real screenshots)
convert -size 1920x1080 xc:skyblue -pointsize 72 -draw "text 800,540 '1. Dashboard'" 1.jpg
convert -size 1920x1080 xc:lightgreen -pointsize 72 -draw "text 800,540 '2. Activities'" 2.jpg  
convert -size 1920x1080 xc:lightcoral -pointsize 72 -draw "text 800,540 '3. Analytics'" 3.jpg
``` 