from xflrpy import Client


class ProjectManager():
    def __init__(self):
        self._client = Client()
        self._state = {
            'project_name': None,
            'project_path': None,
            'saved': None
        }

    @property
    def state(self):
        self._client._update_state()
        return self.state
    
    def _handle_state_change(self, newstate):
        self._state['project_name'] = newstate.project_name
        self._state['project_path'] = newstate.project_path
        self._state['saved'] = newstate.saved

    def create(self, projectPath="", save_current=True):
        """
        Args:
            projectPath: (str, optional) Absolute project path to .xfl file
            save_current (bool, optional): Flag to save the current project

        Returns:
            None
        """
        if save_current:
            self.save()
        self._client.call("newProject")
        if projectPath != "":
            if projectPath[-4:] != ".xfl":
                projectPath += ".xfl"
            self.save(projectPath)
        self._client._update_state()

    def open(self, files, save_current=True):
        """
        Args:
            files: (str) Absolute project path to .xfl file / (list) List of .dat airfoil files to open 
            save_current (bool, optional): Flag to save the current project

        Returns:
            None
        """
        if save_current:
            self.save()
        if type(files) == str:
            files = [files]
        if files is None:
            print(
                "{1}: Please provide valid file(s). Accepted file formats: .xfl, .dat, .wpa,  ".format(files))
        else:
            # TODO:
            # Validate file/files exist, else throw exception
            # If XFL file, validate it is sole file
            # Allow Multiple DAT FILES
            self._client.call('loadProject', files)
        self._client._update_state()

    def save(self, path=None) -> None:
        """
        Save the project.
        Args:
            path: (str, optional) Absolute project path to .xfl file
                         if empty, the current project will be saved
        Returns:
            None
        """

        if path:
            self._client.call("setProjectPath", path)
        elif not self.state['project_path']:
            print("Current project is empty. Please save with a valid path")
            return
        self._client.call("saveProject")
        self._client._update_state()

    def close(self):
        """
        Cleanly exit the server thread and close the gui as well. 

        Returns:
            None
        """
        print("Closing Xflr client and server")
        self._rpc_client.call("exit")

    def __str__(self):
        project_summary = ""
        if self.state['project_name']:
            project_summary += "project=" + self.state['project_name'] + ', '
        if self.state['saved']:
            project_summary += "status=saved"
        else:
            project_summary += "status=not saved"

        return f"<ProjectManager>({project_summary})"
