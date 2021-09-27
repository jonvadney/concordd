Concord 4 Home Automation Home Assistant Integration
=============================

This packge implements the Home Assistant API developed by [JasonCarter80](https://github.com/JasonCarter80) using the concordd to retrieve data from the GE Concord 4 RS232 Automation Module. 

## Known Issues ##
- Only Binary Sensors are currently functional. 
  - The Alarm Control Panel part of the Concord232 Integration doesn't apear to send key press notifications, and alarm doesn't allow specifying codes.  

## Roadmap ##
- Add support for alarming & keypad
- Figure out how to fix the Home Assist Alarm Control Panel 
- Create Docker images for installation 
- Add installation & running doc

## Dependencies ##
concordd must be running

## Installing, and running ##
TODO: Add Doc

## License ##
Apache 2.0

## Links ##
[Original Concord232](https://github.com/JasonCarter80/concord232)
[Home Assistant Concord232 Integration](https://www.home-assistant.io/integrations/concord232/)
