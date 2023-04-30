# The last version control you will ever need - only for Blender!

No more making copies of your blender project with arbitrary namings, only to forget what is exactly inside them. Checkout features

**INSERT PRESENTATION VIDEO IN FIRESHIP STYLE (BLENDER BACKUP IN 100 SECONDS)**

## Features

- Automatically start version control on new projects (toggleable): (insert gif)
- Quickly save a backup after each save with the backup dialog (toggleable): (insert gif)
- Browse through all saved backups of the current project in the Version Control panel: (gif)
- Go back to a save point at any time, and continue development without any trouble.
- Want to go back and make serious changes from further saves? Initialize a new timeline, and work from the selected starting point
- Select if previous saves should go along with the new timeline or not
- Easily add, edit, or remove timelines!
- Clear unnecessary saves from the history by removing them\*
  \*This won't delete the backup from disk, see more details [**here**](sasd)
- Check how much storage space your backups are taking with each new save
- Finished project and want to clear out backups? Just head over to preferences and delete version control from the project. Done.
- Want to save versions of textures/materials or other assets along with the project? You got it! check out [**here**](asdasd) how to make it work

## How to use it

Plain and simple. Download the addon and install it like any other. Done!

**Note**: The first time you activate it, it will take some time to load.
**For Windows**: Run Blender as administrator the first time you install Blender Backup in the desired Blender version. ([click here for details](details)).

There's also a known bug if you are running Blender in portable mode (zip). [Click here](Click%20here) to know more about how to get around that.

## How it works

### Future changes roadmap

- [ ] Checkpoints of individual objects inside the Scene - 2.0
- [ ] Cloud services integration - 2.0
- [ ] Custom Icons - 2.0 junto com achievements
- [ ] GAMEFICAR O PROCESSO TODO, ADICIONANDO "ACHIEVEMENTS" PARA CERTAS METAS ALCANÇADAS - 2.0
- [ ] Achievements using "Menu List" from "Add Curve: extra objects" Addon - or rather, a grid-like, showin the achievements and icons, with the description of the achievement when unlocked and hovered - 2.0
- [ ] Checkbox to delete checkpoint from all timelines altogether
- [ ] handle multiple projects under the same folder

- [x] MAKE HELPER FUNCTION TO CHECK IF FILE NAME CHANGED AND WARN USER - Check if filename é o mesmo que está no state, caso contrário, exibir warning do erro e não exibir as listagens - ACTUALLY, ask user if that is intended and display button to update it on persisted state if yes to correctly manage files - fácil
- [x] Button in preferences to delete unused checkpoints - fácil - actually implemented it in such a way that when deleting checkpoint it searches other timelines to see if it is being used, if not then we remove the saved file
- [x] Search for backups by description - médio - actualy really easy

- [x] Action button to edit selected save description - fácil
- [x] Action button to export selected checkpoint - fácil
- [x] Make checkpoints accessable from file explorer (Also improving "remove checkpoint" action, enabling it to delete the checkpoint from disk) - fácil (junto com o debaixo)
- [x] Button to retrieve/"export" selected checkpoint, generating a folder outside ".checkpoints" with all the files inside the selected checkpoint, for easy retrieval of the desired checkpoint, without needing the user to manually enter the folder and figure out where it is the checkpoint he wants - fácil
- [x] Editable file/folder(s) pattern that gets versioned along with project (instead of just "/textures" folder) - MÉDIO - Actually we could make it so that blender packs the external files that are in the mentioned folders (!!) - This would make it so I don't need to turn the saves into folder that contain the files, it would all be inside the .blend file (!!) - Actually, I don't even need this, user can just pack files as needed, and then unpack then when exporting the .blend file to get access to them easily (!!!!!!!!!!!!!!!!)
- [x] Refactor addon for Blender 2.8 - only if desired by community - FEITO COM REFATORAÇÃO

- [ ] Auto updater - maybe, probably not necessary - DROPPED
- [ ] Automatic incremental version counter with control for major versions (v1.0, v1.1, v1.2... v2.0, v2.1... etc) - DROPPED
- [ ] Warning para quando o Blender está com Packed files, avisando os checkpoints podem consumir bastante espaço por conta disso - Not possible, there isn't any API for that - CANCELLED
- [ ] Display preview image of the checkpoint - DROPPED
