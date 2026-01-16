import os
from datetime import datetime
import cv2

class file_save_handler:
    
    # constructor
    def __init__(self, notes_callback=None):
        """ Initializes the file save handler by creating a base results directory. """
        self.base_directory = "results"
        os.makedirs(self.base_directory, exist_ok=True)
        self.current_folder = None
        self.txt_file_path = None
        self.video_writer = None
        self.csv_file_path = None
        self.notes_callback = notes_callback
        self.current_folder = None
        self.txt_file_path = None

    # method creates a new folder under /results/
    def create_new_folder(self, folder_name=None):
        """ Creates a new folder inside the base results directory."""
        if self.current_folder is None:
            if folder_name is None:
                folder_name = datetime.now().strftime("%Y%m%d_%H%M%S")

            self.current_folder = os.path.join(self.base_directory, folder_name)
            os.makedirs(self.current_folder, exist_ok=True)

            print(f"Created new folder for logs: {self.current_folder}")
            self.__create_txt_file()
            self.__create_csv_file(folder_name)

    # private method - creates a .txt file in the current folder
    def __create_txt_file(self):
        """ Creates a log.txt file in the current folder. """
        if not self.current_folder:
            raise RuntimeError("No folder created yet.")
        
        self.txt_file_path = os.path.join(self.current_folder, "log.txt")
        open(self.txt_file_path, "w").close()  # create empty log.txt

    # adds a line of text to the txt file
    def add_log_to_txt(self, text: str):
        """ Appends a line of text to the log.txt file in the current folder. """
        if not self.txt_file_path:
            raise RuntimeError("No txt file created yet.")

        with open(self.txt_file_path, "a", encoding="utf-8") as f:
            f.write(text + "\n")

    # adds an image to the current folder
    def add_image_log(self, frame, image_name: str):
        """ Saves an image frame to the current folder with the specified image name. """
        if not self.current_folder:
            raise RuntimeError("No folder created yet.")
        
        if not image_name.lower().endswith((".jpg", ".png", ".jpeg")):
            image_name += ".jpg"
        
        save_path = os.path.join(self.current_folder, image_name)
        cv2.imwrite(save_path, frame)
        if self.notes_callback:
            self.notes_callback(f"Saved image: {save_path}")
    
    # video logging methods
    def start_video_log(self, filename="output.mp4", fps=10, frame_size=(1020, 600)):
        """ Starts video logging by creating a VideoWriter object. """
        video_path = os.path.join(self.current_folder, filename)
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        self.video_writer = cv2.VideoWriter(video_path, fourcc, fps, frame_size)
        return video_path
    
    # method to add a frame to the video
    def add_frame_to_video(self, frame):
        """ Write a single frame to the open video log """
        if self.video_writer is not None:
            self.video_writer.write(frame)

    # method to stop video logging
    def stop_video_log(self):
        """ Stops video logging by releasing the VideoWriter object. """
        if self.video_writer is not None:
            self.video_writer.release()
            self.video_writer = None
    
    def __create_csv_file(self, csv_file_name=None):
        """ Creates a CSV file in the current folder. """
        if not self.current_folder:
            raise RuntimeError("No folder created yet.")
        
        if csv_file_name is None:
            csv_file_name = "data.csv"
        elif not csv_file_name.lower().endswith(".csv"):
            csv_file_name += ".csv"

        self.csv_file_path = os.path.join(self.current_folder, csv_file_name)
        open(self.csv_file_path, "w").close()  # create empty csv file
    
    def create_radar_csv(self, csv_file_name="radar_log.csv"):
        """ Creates a radar CSV file in the current folder. """
        if not self.current_folder:
            raise RuntimeError("No folder created yet.")
        self.radar_csv_path = os.path.join(self.current_folder, csv_file_name)
        open(self.radar_csv_path, "w").close()
        print(f"Created radar CSV file: {self.radar_csv_path}")
        return self.radar_csv_path

    def add_radar_row(self, row_data: str, csv_path: str = None):
        """ Appends a row of data to the radar CSV file. """
        if not self.current_folder:
            raise RuntimeError("No folder created yet.")
        path = csv_path or getattr(self, "radar_csv_path", None)
        if path is None:
            raise RuntimeError("No radar csv file created yet.")
        with open(path, "a", encoding="utf-8") as f:
            f.write(row_data + "\n")

    def add_row_to_csv(self, row_data: str):
        """ Appends a row of data to the main CSV file. """
        if not self.current_folder:
            raise RuntimeError("No folder created yet.")
        
        if self.csv_file_path is None:
            raise RuntimeError("No csv file created yet.")
        
        with open(self.csv_file_path, "a", encoding="utf-8") as f:
            f.write(row_data + "\n")
