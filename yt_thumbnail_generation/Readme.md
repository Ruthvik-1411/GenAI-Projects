# Youtube Thumbnail Generation
The idea is to create an application where a youtube video url can be taken as input and a fitting thumbnail can be generated for that video based on it's content. The recommended images will be generated using LLMs. 

Youtube Thumbnail Generator will do all this in less than a minute and also allows editing of the artifacts generated during the process such as the video description, prompts that were generated. So, if the final image is not as expected, edits can be made to these prompts and all subsequent steps will be run again to get the desired image. 

Once a final thumbnail is generated, more edits can be made on top of this image, such as adding some text, changing background colours and many more. All this can be done via chat, just ask and the bot will generate a new image with the requested changes.

### Workflow
This application needs two inputs:
1. `Gemini API Key` - This can be obtained from Google AI Studio, as Google is pretty generous with the quota & rate limits for their free tier. (Note: To use Imagen model for image generation an API key with billing is required, as imagen is not available in free tier.)
2. `Youtube Video URL` - The url of the video for which thumbnail is needed.

**High level overview:**
<img src="https://github.com/Ruthvik-1411/GenAI-Projects/blob/main/yt_thumbnail_generation/assets/yt_thumbnail_arch.png">
#### Video Processing
The first step of the application is processing the video from youtube. For this `yt-dlp` library is used. This library handles downloading of the mp3 and mp4 in the requested formats from youtube without any key or authentication(not sure if it's a proper method but it's open source...). After dowloading the data, they are combined together using ffmpeg.
  * Youtube video can be high quality and longer, so processing it would take a lot of time. To handle this, we can split the processing into two ways,
    * Video duration > 2 mins: We download the audio, video and combine them. This will be the data that will be used to generate description of the video. `Format: mp4 with high quality audio + video.`
    * Video duration < 30 mins: We download only the video into a temp file and take snapshots of the video at equal intervals of time, say start, middle and end. Based on the number of snapshots, the video is processed and the snapshots of the video will be used to generate description of the video. `Format: N Snapshots of video taken at different points of time.`
    * For now video greater than 30 mins is not considered, since it would take a long time to download the content.
  * Apart from the actual video content, the metadata is also extracted using yt_dlp, some fields of interest are video title, description, category, tags and english subtitles if present. These fields tell a lot about the video that might not be clear from the video or snapshots alone.
#### Video Analysis
After getting the video data and metadata, a high level description of the video is generated using text generation models. Gemini-2.0-flash is used with a carefully crafted prompt, that provides a 2-3 sentences description of the video. Based on the media type we have, if video, it's passed as is, since video input is also processed by the Gemini API, for snapshots the images are passed one after another.

The [video analysis prompt](https://github.com/Ruthvik-1411/GenAI-Projects/blob/main/yt_thumbnail_generation/src/core/prompts.py#L4) was revised to give a rather vague description of the video, for instance - if the video is a demo of a new chat application that let's you chat with your csv, using python, langchain or some other technology, the video description abstracts all the tech jargon, specific details and provides a general and tech agnostic view of the video.

#### Prompt Generation
Utilizing the video description that's generated, as input, a text prompt will be generated using the [image generation prompt](https://github.com/Ruthvik-1411/GenAI-Projects/blob/main/yt_thumbnail_generation/src/core/prompts.py#L41). This prompt as well is revised multiple times to add a lot of elements into the final text prompt that will be used by image generation models to generate the desired image. A lot of elements like element of focus, background style, stylistic information, camera style, element placement in the image etc are described in the generated text prompt. This helps the image generation models to create an image as needed. The text prompt that's generated can be modified if it's missing some details or if additional fluff is added, that can edited and removed as well in the UI.

#### Image Generation
After the text prompt is finalized, it's passed to the image generation models as input with some additional generation config, such as aspect ratio, mime_type etc. Google currently has two models that support image generation:
  * **Imagen x(1/2/3)**: Imagen models can be used to generate high quality image in different styles, upscale images, edit images. They are costly and not usually available in free tier.
  * **Flash 2.0 Image Generation(Image out)**: This is a new model in the gemini family currently in preview, which generates 'Image' in the output in addition to text unlike traditional LLMs. This model natively outputs image, instead of using other tools for image generation. This is available in free tier.

The generated image is saved once it's generated and can be downloaded from the UI. If the image is not as per expectations, the text prompt in the previous step can be modified after identifying the shortcomings and new image can be re-generated. This process can be continued until a good enough image is generated.

#### Image editing
Once a final thumbnail is generated and it looks okay, minor additions can be requested via chat. Changing the text prompt might not always give better results as image generation models use diffusion to generate content, each iteration would give a rather different image. 

So instead of modifying the text prompt, for changes like background colour change, text addition and minor edits in the image such as erasing some background elements flash 2.0 Image genertion model can be used to make these edits on the base image.

In the chat space, simple prompts can be provided, like "Add abc text with black font and thick width on the right side", "remove the moon in the image" etc and this model will generate the edited images and after multiple back and forth via chat, if the image is satisfactory, it can be downloaded.


### Installation and Development
1. Clone the repo using
   ```
   git clone https://github.com/Ruthvik-1411/GenAI-Projects.git
   ```
2. Navigate to the src folder
   ```
   cd GenAI-Projects/yt_thumbnail_generation/src
   ```
3. Create a venv based on your device (Windows/Linux/MacOS)
   ```
   python -m venv venv
   venv\Scripts\activate or source venv/bin/activate
   ```
4. Install the required packages using
   ```
   pip install -r requirements.txt
   ```
> Additional Installations: ffmpeg<br> <li>https://www.ffmpeg.org/download.html</li><li> https://www.gyan.dev/ffmpeg/builds/</li>
5. From the src folder, run the streamlit app using,
   ```
   streamlit run app.py
   ```
6. Browser tab will auto open or open the localhost:8051 port in the browser and the app will be live. Add in the Gemini API Key in the left sidebar and provide the youtube video url to the application and click on begin workflow button. Change the prompt generation, image generation models and number of snapshots as needed.

> Feel free to add your own logic on top of this or remove any redundacies in the codebase. One feature that was missed out was to add a refine option to let another model modify the text generated for image generation, since humans are the end users and need to review the thumbnail, it would be fit for humans to make these changes rather than the bot.
### Screenshots
(Video demos coming soon)

Following are some screenshots for the overall application and each step in the process. Click on the image to see it in more detail.

**Overall View**:
<img src="https://github.com/Ruthvik-1411/GenAI-Projects/blob/main/yt_thumbnail_generation/assets/overall.png">
**Step by step View**:
<table>
  <tr>
    <td><img src="https://github.com/Ruthvik-1411/GenAI-Projects/blob/main/yt_thumbnail_generation/assets/step1.png" width="450"/></td>
    <td><img src="https://github.com/Ruthvik-1411/GenAI-Projects/blob/main/yt_thumbnail_generation/assets/step2.png" width="450"/></td>
  </tr>
  <tr>
    <td><img src="https://github.com/Ruthvik-1411/GenAI-Projects/blob/main/yt_thumbnail_generation/assets/step3.png" width="450"/></td>
    <td><img src="https://github.com/Ruthvik-1411/GenAI-Projects/blob/main/yt_thumbnail_generation/assets/step4.png" width="450"/></td>
  </tr>
  <tr>
    <td><img src="https://github.com/Ruthvik-1411/GenAI-Projects/blob/main/yt_thumbnail_generation/assets/step5.png" width="450"/></td>
    <td><img src="https://github.com/Ruthvik-1411/GenAI-Projects/blob/main/yt_thumbnail_generation/assets/sample_thumbnail.png" width="450"/></td>
  </tr>
</table>
