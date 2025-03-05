# Corpus Data of CuRIAM

The corpus data is available in `JSON` format. The JSON is a list of the 41 annotated opinion `documents`. 
* Each `document` consists of a `name` and as a list of annotated `sentences`.
* Each `sentence` has `id` and the list of `tokens`. 
* Each `token` has an `id` and `text` and has `annotation`s (considered unordered for now).
* Each `annotation` has an `id` indicating a BIO indication of the tagged chunk since labels can overlap.

Below is a reference structure.

```
[{
    "name": "<document>"
    "sentences": [
        {
            "id" : "<id>",
            "tokens" : [
                {
                    "text": "<text>",
                    "annotations": [
                        {
                            "id" : "<BIO tag>",
                            "category" : "<Curium-Category>"
                        }
                    ]                   
                }
            ]           
        }
    ]   
}]
```
 