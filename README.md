# VAM Story Builder

While VAM is great for creating individual scenes, I find it's not very good for creating stories.  Scene loading is slow and while merge-loading is faster, it requires each scenes atoms to be compatible with each other.  In addition to that it's hard to do any character development when your interactions are limited to purely physical.

This is where VAM Story Builder comes in.  It solves these particular issues, allowing for fast switching of scenes and a dialog system that can be anything from a simple exchange to a complex and recursive response tree.

This is a command line tool that uses configuration files to create/update scenes and features the following:

* *Merge-Load Compatibility* - Compares and supplements scenes with missing atoms.
* *Project Scaffolding* - Quickly build scene templates with pre-configured atoms.
* *Dialog System* - Uses JSON generated from [Twine](https://twinery.org/2) to create dynamic dialog trees.

### Install

1. Download the latest zip from the [releases page](https://github.com/OnePunchVAM/vam-story-builder/releases) and extract it to somewhere on your computer.
2. Navigate to the extracted directory `vam-story-builder`.
3. Edit `config.json` and make sure `VAM_PATH` matches the install location of your VAM application.

> It's important to note that the double backslashes `\\` in the path are required since it's a json file.



## Merge-Load Compatibility

VAM's merge-load feature is great for speedy transitions between scenes.  Unfortunately it doesn't truncate atoms that are no longer required during a merge-load, and allows for artifacts to be carried over between scenes.

I'll often refer to scaffolding in my docs.  What I mean by this is to make a series of scenes merge-load compatible.

> To make two (or more) scenes merge-load compatible, they must all have the same or similar atoms.

### The Problem

Consider these two scenes with the following atoms.

```
SceneA
---------------------------------
Jack (Person)
Jill (Person)
LampLight (InvisibleLight)
Environment (CustomUnityAsset)
```

```
SceneB
---------------------------------
Jill (Person)
Toy (CustomUnityAsset)
CeilingLight (InvisibleLight)
Environment (CustomUnityAsset)
``` 

In this situation if you were to load **SceneA** normally, then merge-load **SceneB** you would end up with the following result.

```
MergedScene
---------------------------------
Jack (Person)
Jill (Person)
Toy (CustomUnityAsset)
LampLight (InvisibleLight)
CeilingLight (InvisibleLight)
Environment (CustomUnityAsset)
```

As you can tell there are a number of issues here.  We wanted to load **SceneB** but due to how merge-load works we ended up with atoms in the scene that we didn't intend for.  This problem compounds with each merge-load you do, ending up with a spaghetti mess of atoms in your scene.

### The Solution

To combat this problem, VAM Story Builder will take all the scenes in a project and compare their atoms.  It then **creates new scene files** with all atoms from sibling scenes but hidden.


```
SceneA (Generated)
---------------------------------
Jack (Person)
Jill (Person)
Toy (CustomUnityAsset) [HIDDEN]
LampLight (InvisibleLight)
CeilingLight (InvisibleLight) [HIDDEN]
Environment (CustomUnityAsset)
```

```
SceneB (Generated)
---------------------------------
Jack (Person) [HIDDEN]
Jill (Person)
Toy (CustomUnityAsset)
LampLight (InvisibleLight) [HIDDEN]
CeilingLight (InvisibleLight)
Environment (CustomUnityAsset)
``` 

This allows for merge-load compatibility across the two scenes, and this system can be extended to as many scenes as you want.  The side-effect is that you have a longer load time for the first scene you load as it will have a lot of hidden atoms that aren't required.  But once loaded merge-loads will happen quickly and flawlessly.



## Project Scaffolding

When a project is built it will try to find directory that corresponds with the project name in your VAM scenes folder (ie, `VAM/Saves/scene/PROJECT_NAME`).  If found it will create a copy of it with `.scaffold` appended to the end of the folder name (ie, `VAM/Saves/scene/PROJECT_NAME.scaffold`).  Otherwise it will create an empty scaffold directory.

All projects are defined with a configuration file `blueprint.json`.  Scenes are only processed if defined in the projects blueprint.  Check the projects folder `vam-story-builder/projects` for examples.

### Creating a Project

Simply create a directory with the name of your project in `vam-story-builder/projects` and add a `blueprint.json` file.

#### Example

**Project Blueprint:** `vam-story-builder/projects/my-project/blueprint.json` 

```
{
  "scenes": [
    "SceneA.json",
    "SceneB.json",
    "SceneC.json
  ]
}
```

**Existing Project Files:**

```
VAM/Saves/scene/my-project/SceneA.json
VAM/Saves/scene/my-project/SceneB.json
VAM/Saves/scene/my-project/my-image.jpg
```

**Generated Output:**

```
VAM/Saves/scene/my-project.scaffold/SceneA.json
VAM/Saves/scene/my-project.scaffold/SceneB.json
VAM/Saves/scene/my-project.scaffold/SceneC.json
VAM/Saves/scene/my-project.scaffold/my-image.jpg
```



### Scene Packaging

Built on top of this is the scene packaging system.  This allows you to extract an atom, or group of atoms from a scene and save them as a package.  Look to the `vam-story-builder/templates/packages` folder for examples on what can be done with it.

The best example would be the `Nav` package.  This is a collection of image panels, buttons and text all aligned in a way that creates a large menu (similar to the EasyMate main menu).

The added advantage of the package system is the ability to seed many scenes with the same atoms quickly.  Say you needed a story that contained 4 scenes that all had similar assets.  Using the packaging system you would be able to quickly scaffold these scenes with the required atoms in very little time.  Each scene would be consistant and provide an excellent starting point to flesh the scene out.  If you ever need to expand the number of packages or scenes, this can be done at any time while maintaining any work that has been done in the interim.

#### Example

**Project Blueprint:** `vam-story-builder/projects/my-project/blueprint.json` 

```
{
  "packages": [
    "Environment": 1,
    "Light": 2,
    "Girl": 1,
    "Toy": 3
  ],
  "scenes": [
    "SceneA.json",
    "SceneB.json",
    "SceneC.json",
    "SceneD.json"
  ]
}
```

**Existing Project Files:** None

**Generated Output:**

```
VAM/Saves/scene/my-project.scaffold/SceneA.json
VAM/Saves/scene/my-project.scaffold/SceneB.json
VAM/Saves/scene/my-project.scaffold/SceneC.json
VAM/Saves/scene/my-project.scaffold/SceneD.json
```

**Scene Atoms**

```
Environment
Light
Light#2
Girl
Toy
Toy#2
Toy#3
```


## Dialog System 

The dialog system uses [Twine](https://twinery.org/2) for writing the dialog and dialog prompts.  It's a simple gui that allows you to map out dialogs in pretty much any way you want.

The architecture behind the dialog system relies on scanning your Twine json and figuring out how many "branches" (ie, nodes before a dialog prompt) there are.

It fully supports keeping scene trees as they originally were.  The entire thing runs on an AnimationPattern per "Branch" of the tree.  Each branch has animation triggers at particular times that fire off new dialog or configure and show the prompt.

You can even modify the existing triggers in the branches and add your own actions (ie, adding custom Timeline animations at particular points in the conversation).

The script intelligently figures out which things to change and what not to.  So you can update the dialog in your Twine dialog tree, pump the new JSON into this tool and it will intelligently update your conversation flows while keeping any changes or additions you have made.

The architecture behind the dialog system relies on scanning your Twine json and figuring out how many "branches" (ie, nodes before a dialog prompt) there are.
 
On top of that it also dynamically creates the correct number of buttons for the maximum amount of choices that can display on the screen at a time.  Button text, color is set via the twine dialog tree.    

In order to get the button prompts to dynamically select the next branch to play you will need [JayJayWon's ActionGrouper](https://www.patreon.com/posts/actiongrouper-v1-35041756).

### Twine Dialog Structure

Turn this:

![Twine Dialog Overview](/images/twine.jpg)

![Twine Node Editing](/images/twine_node.png)
![Twine Node Editing](/images/twine_node_prompt.png)

And turn it into this:

![Dialog Ingame](/images/dialog_ingame.jpg)


#### Naming

Treat the name of each node as a unique id.  When this tool updates an existing scene to determine if new dialog needs to be added, removed or rewired; it uses the name of each node as it's reference.

#### Tagging

Tagging is important.  It's tells my script what to do at certain points while building the dialog tree.  Here are some examples of tags that work. 

`delay` `5.0` - do nothing for 5 seconds
 
`Person` `says` - atom with id Person#1 gets a SpeechBubble 

`Person#3` `thinks` - atom with id Person#1 gets a ThoughtBubble

`Person` `says` `6.4` - atom with id Person#1 gets a SpeechBubble with a Lifetime of 5 seconds

`Person#2` `says` `prompt` - atom with id Person#1 gets a ThoughtBubble and the user is shown dialog choices 

#### Links

Included in the body text of your Twine nodes is where you add references to other nodes for the dialog tree to follow or prompt the user (only if the `prompt` tag is present).

#### Output to JSON
Once you have your dialog created you will need to export it to json.  In order to do that you will have to add the twinson output format.

Taken from https://github.com/lazerwalker/twison

> From the Twine 2 story select screen, add a story format, and point it to the url https://lazerwalker.com/twison/format.js.  


#### Example

**Twine Dialog:** [here](https://twinery.org/2/#!/stories/bac4ce2b-79e1-4669-9182-662f7365b7b4)

**Project Blueprint:** `vam-story-builder/projects/my-project/blueprint.json` 

```
{
  "packages": [
    "Environment": 1,
    "Light": 1,
    "Girl": 1
  ],
  "scenes": [
    {
      "scene_path": "SceneA.json",
      "dialog_path": "SceneA_dialog.json"
    }
  ]
}
```

**Existing Project Files:** None

**Generated Output:**

```
VAM/Saves/scene/my-project.scaffold/SceneA.json
```

**Scene Atoms**

> *Assuming the dialog file `SceneA_dialog.json` had a maximum of 2 choices for dialog prompts and 4 dialog branches.*

```
Environment
Light
Girl
Dialog
Dialog-StartBtn
Dialog-Choices
Dialog-Branch#1
Dialog-Branch#1-Duration
Dialog-Branch#2
Dialog-Branch#2-Duration
Dialog-Branch#3
Dialog-Branch#3-Duration
Dialog-Branch#4
Dialog-Branch#4-Duration
```