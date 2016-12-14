# OpenCV Motorized Autofocus on Raspberry Pi 3

This project mostly was created within a one day Hackathon with the aim to create an autofocus lense on a Basler dart camera controlled by an Raspberry Pi.

With this project we basically wanted to solve two problems:
First we wanted to be able to control a motorized lense's zoom, iris and focus stepper motors with a simple python class. And second we wanted to be able to try some different autofocus algorithms on it.
And if that wouldn't be enough for just roughly one day, we wanted all of that to work on a Raspberry Pi 3! 

So this project will give you access to a Python class which you can use to control a similar lens with some stepper motors on it. For that you will also need an stepper driver to connect the GPIOs with the stepper motor. You will also find the shemetics and bill of materials of our setup. 

On top of that we created a python application which uses this class to give you a GUI to try different autofocus algorithms. Three of them are already implemented and working well well with a Basler Dart Camera. We have designed an 3D printable mount for the used lense.

#License

Free Software, Hell Yeah!

Copyright and related rights are licensed under the Solderpad Hardware License, Version 0.51 (the “License”); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://solderpad.org/licenses/SHL-0.51. Unless required by applicable law or agreed to in writing, software, hardware and materials distributed under this License is distributed on an “AS IS” BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

