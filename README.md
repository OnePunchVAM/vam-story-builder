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

In this situation if you were to load *SceneA* normally, then merge-load *SceneB* you would end up with the following result.

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

As you can tell there are a number of issues here.  We wanted to load *SceneB* but due to how merge-load works we ended up with atoms in the scene that we didn't intend for.  This problem compounds with each merge-load you do, ending up with a spaghetti mess of atoms in your scene.

### The Solution

To combat this problem, VAM Story Builder will take all the scenes in a project and compare their atoms.  It then *creates new scene files* with all atoms from sibling scenes but hidden.


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

*Project Blueprint:* `vam-story-builder/projects/my-project/blueprint.json` 

```
{
    "scenes": [
        "SceneA.json",
        "SceneB.json",
        "SceneC.json
    ]
}
```

*Existing Project Files:*

```
VAM/Saves/scene/my-project/SceneA.json
VAM/Saves/scene/my-project/SceneB.json
VAM/Saves/scene/my-project/my-image.jpg
```

*Generated Output:*

```
VAM/Saves/scene/my-project.scaffold/SceneA.json
VAM/Saves/scene/my-project.scaffold/SceneB.json
VAM/Saves/scene/my-project.scaffold/SceneC.json
VAM/Saves/scene/my-project.scaffold/my-image.jpg
```

#### Advanced Example

*Project Blueprint:* `vam-story-builder/projects/my-advanced-project/blueprint.json` 

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
        {
            "scene_path": "SceneC.json",
            "dialog_path": "SceneC_dialog.json"
        }
    ]
}
```

*Existing Project Files:* None

*Generated Output:*

```
VAM/Saves/scene/my-advanced-project.scaffold/SceneA.json
VAM/Saves/scene/my-advanced-project.scaffold/SceneB.json
VAM/Saves/scene/my-advanced-project.scaffold/SceneC.json
```

*Scene Atoms*

```
Environment
Light
Light#2
Girl
Toy
Toy#2
Toy#3
```



### Scene Packaging

_tbd_


## Dialog System 

_tbd_