# Transcript API

This folder will be reponsible for the Transcript API.  
Once Typesense completes its search, this API will translate its results into a JSON package to send to the front-end and display to the user.  
The package has the following information in it:
```json
{
    "video_id": "<video_id>",
    "title": "video_title",
    "instances": [
        
    ]
}
```

For example, the search query would be "all" within the following video.  
[![Me at the zoo](https://img.youtube.com/vi/jNQXAC9IVRw/0.jpg)](https://www.youtube.com/watch?v=jNQXAC9IVRw).  
The package would be:
```json
{
    "video_id": "jNQXAC9IVRw",
    "title": "Me at the zoo",
    "instances": [
        1,
        17
    ]
}
```
