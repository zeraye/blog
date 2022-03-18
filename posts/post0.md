---
title: Why Meta is terrible company
date: 2022-03-18
---

## Why Meta is terrible company
 
In this post I will share my experience with developing tools for Messenger as an external developer. Mostly I will trash talk Facebook.

For 2 months I have been developing an [Firefox exntesion](https://github.com/Zeraye/facebook-speech-recognition) for transcribing voice messages (STT). In the very beginning I though the worst part will be properly working machine learning model for Polish language. I'm from Poland, so such transcription was really important for me. After some research I found German, English, Spanish, French, Italian and Polish models. They were not working great, but quite nice for the start.

The second part was to create the extension. That was the most frustrating programming experience in my life. Messenger just hate external developers. At first there isn't any offical API for receiving and sending messages. Everything I do must be done via modyfing DOM elements. Facebook is build with React, so working on class names to operate on divs won't work. That's okay, you have `querySelector`, so that wasn't such a big problem. Working and chaning DOM elements is a pain in the butt. There is some strange clunky effect. After some struggle I was able to extract audio link to my exntesion, do some magic on it and return transcription. Now I have to create artificial message. First idea was just to copy nearest text message and use it as a template. But what if there isn't any? I know it's rare, but I wanna point out that you can't do it. Without a mock text message you aren't able to create a new one. I solved it in this way: if there is a mock text message use it, otherwise create a raw one (colors, border and some other visual stuff won't be implemented). This raw message doesn't suit chat theme, but works.

I have left developing this extension for 5 months. After that time I returned, because new models for transcription showed up. The old ones were temporarily. I couldn't train models on my own, because it's impossible to do it on the personal computer. I don't want to left my only PC for like 6 months straight all day long. Great! Now I can use new models and release extension, right? No. Facebook deleted the `<audio>` tag from voice messages. Recordings are now hidden from the developer. I'm sure there is a way to get audio from the message, but Facebook don't want me to do it. They permamently make my life harder. I won't be fighting again. I quit developing this addon.

Why they can't make working on DOM easier or leave it as it is? Why they removed API for receiving and sending messages? It's probably becase of bots. Okay, but it doesn't make any sense for me. I was able to create bot for sending messages on Messenger within 1 day. It's still possible, but just a bit harder. You can't simply edit `<div>` for new message, but there are other ways. I don't want to write it here.

To sum up, they block all things. Working on messages is much harder, because they fight with bots and simultaneously making bot which spams to everyone takes 1 day. Really? I can't create addon, which can help blind people with using Messenger, because it could be potentially dangerous. At the same time creating something really nasty takes just a few hours more.

I want to end with simple:

> "Fuck Facebook. Never again." ~me
