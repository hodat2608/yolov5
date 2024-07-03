import sys
sys.path.append(r'C:\Users\CCSX009\Documents\yolov5')
from tkinter import filedialog
from PIL import Image, ImageTk
import glob
import torch
import mysql.connector
from tkinter import messagebox,simpledialog
import threading
# import stapipy as st
import numpy as np
import concurrent.futures
import cv2
import socket
import time
from PIL import Image,ImageTk
from yaml import load
import socket
from udp import UDPFinsConnection
from initialization import FinsPLCMemoryAreas
import time
from tkinter import messagebox
import tkinter as tk
import shutil
from pathlib import Path
import sys
import os

soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

def removefile():
    directory1 = 'C:/Users/CCSX009/Documents/yolov5/test_image/camera1/*.jpg'
    directory2 = 'C:/Users/CCSX009/Documents/yolov5/test_image/camera2/*.jpg'
    chk1 = glob.glob(directory1)
    for f1 in chk1:
        os.remove(f1)
        print('already delete folder 1')
    chk2 = glob.glob(directory2)
    for f2 in chk2:
        os.remove(f2)
        print('already delete folder 2')


class MySQL_Connection():

    def __init__(self,host,user,passwd,database):
        self.host = host
        self.user = user
        self.passwd = passwd
        self.database = database

    def Connect_MySQLServer(self):
            db_connection = mysql.connector.connect(
            host= self.host,
            user=self.user, 
            passwd=self.passwd,
            database=self.database)                    
            cursor = db_connection.cursor()
            return cursor,db_connection

    def check_connection(self):
        _,db_connection = self.Connect_MySQLServer()
        try:
            db_connection.ping(reconnect=True, attempts=3, delay=5)
            return True
        except mysql.connector.Error as err:
            messagebox.showinfo("Notification", f"Error connecting to the database: {str(err)}")
            return False

    def reconnect(self):
        _,db_connection = self.Connect_MySQLServer()
        try:
            db_connection.reconnect(attempts=3, delay=5)
            cursor = db_connection.cursor()  
            return True
        except mysql.connector.Error as err:
            messagebox.showinfo("Notification", f"Failed to reconnect to the database: {str(err)}")
            return False
        
    @staticmethod    
    def Connect_to_MySQLServer(host,user,passwd,database):
            db_connection = mysql.connector.connect(
            host= host,
            user=user, 
            passwd=passwd,
            database=database)                    
            cursor = db_connection.cursor()
            return cursor,db_connection
      

class PLC_Connection():

    def __init__(self,host,port):
        self.host = host
        self.port = port
      
    def connect_plc_keyence(self):
        try:
            soc.connect((self.host, self.port))
            return True
        except OSError:
            print("Can't connect to PLC")
            time.sleep(3)
            print("Reconnecting....")
            return False

    def run_plc_keyence(self):
        connected = False
        while connected == False:
            connected = self.connect_plc_keyence(self.host,self.port)
        print("connected") 

    def read_plc_keyence(self,data):
        a = 'RD '
        c = '\x0D'
        d = a+ data +c
        datasend = d.encode("UTF-8")
        soc.sendall(datasend)
        data = soc.recv(1024)
        datadeco = data.decode("UTF-8")
        data1 = int(datadeco)
        return data1

    def write_plc_keyence(self,register,data):
        a = 'WR '
        b = ' '
        c = '\x0D'
        d = a+register+b+str(data)+c
        datasend  = d.encode("UTF-8")
        soc.sendall(datasend)
        datares = soc.recv(1024)

    def connect_plc_omron(self):
        global fins_instance
        try:
            fins_instance = UDPFinsConnection()
            fins_instance.connect(self.host)
            fins_instance.dest_node_add=1
            fins_instance.srce_node_add=25
            return True
        except:
            print("Can't connect to PLC")
            for i in range(100000000):
                pass
            print("Reconnecting....")
            return False

    def run_plc_omron(self):
        connected = False
        while connected == False:
            connected = self.connect_plc_omron(self.host)
            print('connecting ....')
        print("connected plc") 

    def read_plc_omron(self,register):
        register = (register).to_bytes(2, byteorder='big') + b'\x00'
        read_var = fins_instance.memory_area_read(FinsPLCMemoryAreas().DATA_MEMORY_WORD,register)
        read_var = int.from_bytes(read_var[-2:], byteorder='big')  
        return read_var

    def write_plc_omron(self,register,data):
        register = (register).to_bytes(2, byteorder='big') + b'\x00'
        fins_instance.memory_area_write(FinsPLCMemoryAreas().DATA_MEMORY_WORD,register,b'\x00\x00',data)



class Base:

    def __init__(self):
        self.database = MySQL_Connection(None,None,None,None) 
        self.name_table = None
        self.item_code_cfg = None
        self.image_files = []
        self.current_image_index = 0
        self.state = 0
        self.password = " "
        self.lockable_widgets = [] 
        self.lock_params = []
        self.model_name_labels = []
        self.join = []
        self.ok_vars = []
        self.ng_vars = []
        self.num_inputs = []
        self.wn_inputs = []
        self.wx_inputs = []
        self.hn_inputs = []
        self.hx_inputs = []
        self.plc_inputs = []
        self.conf_scales = []
        self.widgets_option_layout_parameters = []
        self.row_widgets = []
        self.weights = []
        self.scale_conf_all = None
        self.size_model = None
        self.item_code = []
        self.make_cls_var = []
        self.permisson_btn = []
        self.model = None
        self.time_processing_output = None
        self.result_detection = None
    
    def connect_database(self):
        cursor, db_connection  = self.database.Connect_MySQLServer()
        check_connection = self.database.check_connection()
        reconnect = self.database.reconnect()
        return cursor,db_connection,check_connection,reconnect
    
    def check_connect_database(self):
        cursor, db_connection = self.database.Connect_MySQLServer()
        if cursor is not None and db_connection is not None:
            print("Database connection successful")
        else:
            print("Database connection failed")
        return cursor, db_connection
    
    def save_params_model(self):
        confirm_save_data = messagebox.askokcancel("Confirm", "Are you sure you want to save the data?")
        cursor,db_connection,check_connection,reconnect = self.connect_database()
        if confirm_save_data:
            try:
                weight = self.weights.get()
                confidence_all = int(self.scale_conf_all.get())
                item_code_value = str(self.item_code.get())
                cursor.execute(f"DELETE FROM {self.name_table} WHERE item_code = %s", (item_code_value,))
                for i1 in range(len(self.model_name_labels)):
                    label_name =  self.model_name_labels[i1].cget("text")
                    join_detect = self.join[i1].get()
                    OK_jont = self.ok_vars[i1].get()
                    NG_jont = self.ng_vars[i1].get()
                    num_labels = int(self.num_inputs[i1].get())
                    width_min = int(self.wn_inputs[i1].get())
                    width_max = int(self.wx_inputs[i1].get())
                    height_min = int(self.hn_inputs[i1].get())
                    height_max = int(self.hx_inputs[i1].get())
                    PLC_value = int(self.plc_inputs[i1].get())
                    cmpnt_conf = int(self.conf_scales[i1].get())
                    query_sql = f"""
                    INSERT INTO {self.name_table}
                    (item_code, weight, confidence_all, label_name,join_detect, OK, NG, num_labels, width_min, width_max, 
                    height_min, height_max, PLC_value, cmpnt_conf)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """
                    values = (item_code_value, weight, confidence_all, label_name, join_detect, OK_jont, NG_jont, num_labels, 
                            width_min, width_max, height_min, height_max, PLC_value, cmpnt_conf)
                    cursor.execute(query_sql,values)
                db_connection.commit()
                cursor.close()
                db_connection.close()
                messagebox.showinfo("Notification", "Saved parameters successfully!")
                model_settings = []
                for i1 in range(len(self.model_name_labels)):
                    model_settings.append({
                        'label_name':  self.model_name_labels[i1].cget("text"),
                        'join_detect': self.join[i1].get(),
                        'OK_jont': self.ok_vars[i1].get(),
                        'NG_jont': self.ng_vars[i1].get(),
                        'num_labels': int(self.num_inputs[i1].get()),
                        'width_min': int(self.wn_inputs[i1].get()),
                        'width_max': int(self.wx_inputs[i1].get()),
                        'height_min': int(self.hn_inputs[i1].get()),
                        'height_max': int(self.hx_inputs[i1].get()),
                        'PLC_value': int(self.plc_inputs[i1].get()),
                        'cmpnt_conf': int(self.conf_scales[i1].get()),
                    })
            except Exception as e:
                cursor.close()
                db_connection.close()
                messagebox.showinfo("Notification", f"Data saved failed! Error: {str(e)}")
        else:
            pass
    
    def processing_handle_image_customize(self, input_image, width, height):
        label_remove,list_label_ng,results_detect,ok_variable = [],[],'ERROR',False
        size_model_all = int(self.size_model.get())
        conf_all = int(self.scale_conf_all.get()) / 100
        input_image = cv2.cvtColor(input_image, cv2.COLOR_BGR2RGB)
        results = self.model(input_image,size_model_all,conf_all)
        table_results = results.pandas().xyxy[0]
        model_settings = [
            {
                'label_name':  self.model_name_labels[i1].cget("text"),
                'join_detect': self.join[i1].get(),
                'OK_jont': self.ok_vars[i1].get(),
                'NG_jont': self.ng_vars[i1].get(),
                'num_labels': int(self.num_inputs[i1].get()),
                'width_min': int(self.wn_inputs[i1].get()),
                'width_max': int(self.wx_inputs[i1].get()),
                'height_min': int(self.hn_inputs[i1].get()),
                'height_max': int(self.hx_inputs[i1].get()),
                'PLC_value': int(self.plc_inputs[i1].get()),
                'cmpnt_conf': int(self.conf_scales[i1].get()),
            }
            for i1 in range(len(self.model_name_labels))
        ]
        settings_dict = {setting['label_name']: setting for setting in model_settings}
        def check_label(i,settings_dict):
            width_result = table_results['xmax'][i] - table_results['xmin'][i]
            height_result = table_results['ymax'][i] - table_results['ymin'][i]
            conf_result = table_results['confidence'][i] * 100
            setting = settings_dict[table_results['name'][i]]
            if setting:
                if setting['join_detect']:
                    if width_result < setting['width_min'] or width_result > setting['width_max'] \
                            or height_result < setting['height_min'] or height_result > setting['height_max'] \
                            or conf_result < setting['cmpnt_conf']:
                        return i
                else:
                    return i
                return None
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = [executor.submit(check_label, i,settings_dict) for i in range(len(table_results.index))]
            label_remove = [f.result() for f in futures if f.result() is not None]
        table_results.drop(index=label_remove, inplace=True)
        name_rest = list(table_results['name'])
        for model_name,setting in settings_dict.items():
            if setting['join_detect'] and setting['OK_jont'] :
                    if  name_rest.count(model_name) != setting['num_labels']:
                        results_detect = 'NG'
                        ok_variable = True
                        list_label_ng.append(model_name)
            if setting['join_detect'] and setting['NG_jont'] :
                    if setting['label_name']  in name_rest:
                        results_detect = 'NG'
                        ok_variable = True
                        list_label_ng.append(model_name)
        if not ok_variable:
            results_detect = 'OK'
        show_img = np.squeeze(results.render(label_remove))
        show_img = cv2.resize(show_img, (width, height), interpolation=cv2.INTER_AREA)
        return show_img, results_detect, list_label_ng

    
    def load_data_model(self):
        cursor, db_connection,_,_ = self.connect_database()
        cursor.execute(f"SELECT * FROM {self.name_table} WHERE item_code = %s", (self.item_code_cfg,))
        records = cursor.fetchall()
        cursor.close()
        db_connection.close()
        if records:
            first_record = records[0]
            load_item_code = first_record[1]
            load_path_weight = first_record[2]
            load_confidence_all_scale = first_record[3]
        return records,load_path_weight,load_item_code,load_confidence_all_scale

    def load_parameters_model(self,model1,load_path_weight,load_item_code,load_confidence_all_scale,records):
        self.weights.delete(0, tk.END)
        self.weights.insert(0, load_path_weight)
        self.item_code.delete(0, tk.END)
        self.item_code.insert(0, load_item_code)
        self.scale_conf_all.set(load_confidence_all_scale)
        for i1 in range(len(model1.names)):
            for record in records:
                if record[4] == model1.names[i1]:

                    self.join[i1].set(bool(record[5]))

                    self.ok_vars[i1].set(bool(record[6]))

                    self.ng_vars[i1].set(bool(record[7]))

                    self.num_inputs[i1].delete(0, tk.END)
                    self.num_inputs[i1].insert(0, record[8])

                    self.wn_inputs[i1].delete(0, tk.END)
                    self.wn_inputs[i1].insert(0, record[9])

                    self.wx_inputs[i1].delete(0, tk.END)
                    self.wx_inputs[i1].insert(0, record[10])

                    self.hn_inputs[i1].delete(0, tk.END)
                    self.hn_inputs[i1].insert(0, record[11])
                    
                    self.hx_inputs[i1].delete(0, tk.END)
                    self.hx_inputs[i1].insert(0, record[12])

                    self.plc_inputs[i1].delete(0, tk.END)
                    self.plc_inputs[i1].insert(0, record[13])

                    self.conf_scales[i1].set(record[14])
        
    def change_model(self,Frame_2):
        selected_file = filedialog.askopenfilename(title="Choose a file", filetypes=[("Model Files", "*.pt")])
        if selected_file:
            self.weights.delete(0,tk.END)
            self.weights.insert(0,selected_file)
            self.model = torch.hub.load('C:/Users/CCSX009/Documents/yolov5','custom', path=selected_file, source='local', force_reload=False)
            for widget in Frame_2.grid_slaves():
                widget.grid_forget()
            self.option_layout_parameters(Frame_2,self.model)
        else:
            messagebox.showinfo("Notification","Please select the correct training file!")
            pass

    def load_params_child(self):
        weight = self.weights.get()
        item_code_value = str(self.item_code.get())
        cursor, db_connection,_,_ = self.connect_database()
        cursor.execute("SELECT * FROM test_model_cam1_model1 WHERE item_code = %s", (item_code_value,))
        records = cursor.fetchall()
        model = torch.hub.load('C:/Users/CCSX009/Documents/yolov5','custom', path=weight, source='local', force_reload=False)
        cursor.close()
        db_connection.close()
        return records,model

    def load_parameters_from_weight(self, records):
        confirm_load_parameters = messagebox.askokcancel("Confirm", "Are you sure you want to load the parameters?")
        if confirm_load_parameters:
            records, model = self.load_params_child()
            try:
                for i1 in range(len(model.names)):
                    for record in records:
                        if record[4] == model.names[i1]:
                            self.join[i1].set(bool(record[5]))
                            self.ok_vars[i1].set(bool(record[6]))
                            self.ng_vars[i1].set(bool(record[7]))
                            self.num_inputs[i1].delete(0, tk.END)
                            self.num_inputs[i1].insert(0, record[8])
                            self.wn_inputs[i1].delete(0, tk.END)
                            self.wn_inputs[i1].insert(0, record[9])
                            self.wx_inputs[i1].delete(0, tk.END)
                            self.wx_inputs[i1].insert(0, record[10])
                            self.hn_inputs[i1].delete(0, tk.END)
                            self.hn_inputs[i1].insert(0, record[11])
                            self.hx_inputs[i1].delete(0, tk.END)
                            self.hx_inputs[i1].insert(0, record[12])
                            self.plc_inputs[i1].delete(0, tk.END)
                            self.plc_inputs[i1].insert(0, record[13])
                            self.conf_scales[i1].set(record[14])
            except IndexError as e:
                print(f"Error loading parameters: {e}")
            except Exception as e:
                print(f"Unexpected error: {e}")

    def handle_image(self,img1_orgin, width, height,camera_frame):
        for widget in camera_frame.winfo_children():
            widget.destroy()
        t1 = time.time()
        image_result,results_detect,label_ng = self.processing_handle_image_local(img1_orgin, width, height,cls=self.make_cls_var.get())
        t2 = time.time() - t1
        time_processing = str(int(t2*1000)) + 'ms'
        img_pil = Image.fromarray(image_result)
        photo = ImageTk.PhotoImage(img_pil)
        canvas = tk.Canvas(camera_frame, width=width, height=height)
        canvas.grid(row=2, column=0, padx=10, pady=10, sticky='ew')
        canvas.create_image(0, 0, anchor=tk.NW, image=photo)
        canvas.image = photo
        canvas.create_text(10, 10, anchor=tk.NW, text=f'Time: {time_processing}', fill='black', font=('Segoe UI', 20))
        canvas.create_text(10, 40, anchor=tk.NW, text=f'Result: {results_detect}', fill='green' if results_detect == 'OK' else 'red', font=('Segoe UI', 20))
        if not label_ng:
            canvas.create_text(10, 70, anchor=tk.NW, text=f'No Label', fill='green', font=('Segoe UI', 20))
        else:
            label_ng = ','.join(label_ng)
            canvas.create_text(10, 70, anchor=tk.NW, text=f'Label: {label_ng}', fill='red', font=('Segoe UI', 20))
        return results_detect       
    

    def detect_single_img(self, camera_frame):
        selected_file = filedialog.askopenfilename(title="Choose a file", filetypes=[("Image Files", "*.jpg *.jpeg *.png")])
        if selected_file:
            for widget in camera_frame.winfo_children():
                widget.destroy()
            width = 480
            height = 450
            self.handle_image(selected_file, width, height,camera_frame)
        else: 
            pass
           
    def detect_multi_img(self,camera_frame):
        selected_folder = filedialog.askdirectory(title="Choose a folder")
        if selected_folder:
            self.image_files = [os.path.join(selected_folder, f) for f in os.listdir(selected_folder) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
            self.current_image_index = 0
            if self.image_files:
                for widget in camera_frame.winfo_children():
                    widget.destroy()
                self.show_image(self.current_image_index,camera_frame)
            else:
                messagebox.showinfo("No Images", "The selected folder contains no images.")
        else:
            pass

    def show_image(self,index,camera_frame):  
        width = 480
        height = 450
        image_path = self.image_files[index]
        self.handle_image(image_path, width, height,camera_frame)

    def detect_next_img(self,camera_frame):
        if self.current_image_index < len(self.image_files) - 1:
            self.current_image_index += 1
            self.show_image(self.current_image_index,camera_frame)
        else:
            messagebox.showinfo("End of Images", "No more images in the folder.")

    def detect_previos_img(self,camera_frame):
        if self.current_image_index > 0:
            self.current_image_index -= 1
            self.show_image(self.current_image_index,camera_frame)
        else:
            messagebox.showinfo("Start of Images", "This is the first image in the folder.")

    def detect_auto(self, camera_frame):
        selected_folder_original = filedialog.askdirectory(title="Choose a folder")
        if selected_folder_original: 
            selected_folder = glob.glob(selected_folder_original + '/*.jpg')
            if not selected_folder:
                pass
            self.image_index = 0
            self.selected_folder_detect_auto = selected_folder
            self.camera_frame = camera_frame
            self.image_path_mks_cls = []
            self.results_detect = None
            def process_next_image():
                if self.image_index < len(self.selected_folder_detect_auto):
                    self.image_path_mks_cls = self.selected_folder_detect_auto[self.image_index]
                    width = 480
                    height = 450
                    self.results_detect = self.handle_image(self.image_path_mks_cls, width, height,camera_frame)
                    self.image_index += 1
                    self.camera_frame.after(500, process_next_image)
                else:
                    print("Processing auto detect complete")
            process_next_image()
        else:
            pass

    
    def logging(self, folder_ok, folder_ng, logging_ok_checkbox_var, logging_ng_checkbox_var, camera_frame, percent_entry,logging_frame):
        selected_folder_original = filedialog.askdirectory(title="Choose a folder")
        selected_folder = glob.glob(os.path.join(selected_folder_original,'*.jpg'))
        width = 480
        height = 450
        self.image_index = 0
        self.selected_folder_logging = selected_folder
        self.logging_frame = logging_frame
        self.percent_entry = percent_entry
        total_images = len(self.selected_folder_logging)
        if not self.selected_folder_logging:
            return
        
        def update_progress(current_index, total_images):
            percent_value = int((current_index + 1) / total_images * 100)
            self.percent_entry.delete(0, tk.END)
            self.percent_entry.insert(0, f"{percent_value}%")

        def process_images():
            for img in self.selected_folder_logging:
                basename = os.path.basename(img)
                if self.image_index < total_images:
                    results_detect = self.handle_image(img, width, height, camera_frame)
                    if results_detect == 'OK':
                        if logging_ok_checkbox_var.get():
                            shutil.move(img, os.path.join(folder_ok.get(), basename))
                    else:
                        if logging_ng_checkbox_var.get():
                            shutil.move(img, os.path.join(folder_ng.get(), basename))
                    self.logging_frame.after(10, update_progress, self.image_index, total_images)
                    self.image_index += 1
                else:
                    messagebox.showinfo("End of Images", "No more images in the folder.")
                    break
            self.percent_entry.delete(0, tk.END)
            self.percent_entry.insert(0, "0%")
        threading.Thread(target=process_images).start()
        
             
    def toggle_state_layout_model(self): 
        if self.state == 1:
            password = simpledialog.askstring("Administrator", "Enter password:", show="*")
            if password == self.password:
                self.state = 0
                self.permisson_btn.config(text="Lock")
                self.toggle_widgets_state("normal")
            else:
                messagebox.showerror("Error", "Incorrect password!")
        else:
            self.state = 1
            self.permisson_btn.config(text="Unlock")
            self.toggle_widgets_state("disabled")

    def toggle_widgets_state(self,state):
        for widget in self.lockable_widgets:
            widget.config(state=state)

    def toggle_state_option_layout_parameters(self):
        for widget in self.lock_params:
            widget.config(state='disabled')

    def pick_folder_ok(self,folder_ok):
        file_path = filedialog.askdirectory(title="Choose a folder")
        if file_path:
            folder_ok.delete(0,tk.END)
            folder_ok.insert(0,file_path)
           
    def pick_folder_ng(self,folder_ng):
        file_path = filedialog.askdirectory(title="Choose a folder")
        if file_path:
            folder_ng.delete(0,tk.END)
            folder_ng.insert(0,file_path)


    def _make_cls(self,image_path_mks_cls,results,model_settings):  
        with open(image_path_mks_cls[:-3] + 'txt', "a") as file:
            for params in results.xywhn:
                params = params.tolist()
                for item in range(len(params)):
                    param = params[item]
                    param = [round(i,6) for i in param]
                    number_label = int(param[5])
                    conf_result = float(param[4])
                    width_result = float(param[2])*1200
                    height_result = float(param[3])*1600
                    for setting in model_settings:
                        if results.names[int(number_label)] == setting['label_name']:
                            if setting['join_detect']:
                                if width_result < setting['width_min'] or width_result > setting['width_max'] \
                                        or height_result < setting['height_min'] or height_result > setting['height_max'] \
                                        or conf_result < setting['cmpnt_conf']: 
                                    formatted_values = ["{:.6f}".format(value) for value in param[:4]]
                                    output_line = "{} {}\n".format(str(number_label),' '.join(formatted_values))
                                    file.write(output_line)
        path = Path(image_path_mks_cls).parent
        path = os.path.join(path,'classes.txt')
        with open(path, "w") as file:
            for i1 in range(len(results.names)):
                file.write(str(results.names[i1])+'\n')
      
    def classify_imgs(self):
        pass    

    # def processing_handle_image_local(self,input_image_original,width,height,cls=False):
    #     label_remove = []
    #     size_model_all = int(self.size_model.get())
    #     conf_all = int(self.scale_conf_all.get())/100
    #     t1 = time.time()
    #     results = self.model(input_image_original,size_model_all,conf_all)
    #     table_results = results.pandas().xyxy[0]
    #     model_names = self.model.names
    #     model_settings = []
    #     for i1 in range(len(self.model_name_labels)):
    #         model_settings.append({
    #             'label_name':  self.model_name_labels[i1].cget("text"),
    #             'join_detect': self.join[i1].get(),
    #             'OK_jont': self.ok_vars[i1].get(),
    #             'NG_jont': self.ng_vars[i1].get(),
    #             'num_labels': int(self.num_inputs[i1].get()),
    #             'width_min': int(self.wn_inputs[i1].get()),
    #             'width_max': int(self.wx_inputs[i1].get()),
    #             'height_min': int(self.hn_inputs[i1].get()),
    #             'height_max': int(self.hx_inputs[i1].get()),
    #             'PLC_value': int(self.plc_inputs[i1].get()),
    #             'cmpnt_conf': int(self.conf_scales[i1].get()),
    #         })
    #     for i in range(len(table_results.index)):
    #         width_result = table_results['xmax'][i] - table_results['xmin'][i]
    #         height_result = table_results['ymax'][i] - table_results['ymin'][i]
    #         conf_result = table_results['confidence'][i] * 100
    #         label_name_tables_result = table_results['name'][i]
    #         for i1 in range(len(model_names)):
    #             for setting in model_settings:
    #                 if label_name_tables_result == model_names[i1] == setting['label_name']:
    #                     if setting['join_detect']:
    #                         if width_result < setting['width_min'] or width_result > setting['width_max'] \
    #                                 or height_result < setting['height_min'] or height_result > setting['height_max'] \
    #                                 or conf_result < setting['cmpnt_conf']:
    #                             label_remove.append(i)
    #                     else:
    #                         label_remove.append(i)
    #     table_results.drop(index=label_remove, inplace=True)   
    #     name_rest = list(table_results['name'])                
    #     results_detect = 'ERROR'
    #     ok_variable = False
    #     list_label_ng = []
    #     for i1 in range(len(model_names)):
    #         for j1 in model_settings:
    #             if model_names[i1] == j1['label_name']:
    #                 if j1['join_detect']:
    #                     if j1['OK_jont']:
    #                         number_of_labels = name_rest.count(model_names[i1])
    #                         if number_of_labels != j1['num_labels']:
    #                             results_detect = 'NG'
    #                             ok_variable = True
    #                             list_label_ng.append(model_names[i1])
    #                     if j1['NG_jont']:
    #                         if j1['label_name'] in name_rest:
    #                             results_detect = 'NG'
    #                             ok_variable = True
    #                             list_label_ng.append(model_names[i1])
    #     if not ok_variable:
    #         results_detect = 'OK'
    #     show_img = np.squeeze(results.render(label_remove))
    #     show_img = cv2.resize(show_img, (width,height), interpolation=cv2.INTER_AREA)
    #     t2 = time.time() - t1
    #     time_processing = str(int(t2*1000)) + 'ms'
    #     if cls:
    #         self._make_cls(input_image_original,results,model_settings)
    #     return show_img,time_processing,results_detect,list_label_ng
    
    def processing_handle_image_local(self, input_image_original, width, height,cls=False):
        label_remove,list_label_ng,results_detect,ok_variable = [],[],'ERROR',False
        size_model_all = int(self.size_model.get())
        conf_all = int(self.scale_conf_all.get()) / 100
        results = self.model(input_image_original,size_model_all,conf_all)
        table_results = results.pandas().xyxy[0]
        model_settings = [
            {
                'label_name':  self.model_name_labels[i1].cget("text"),
                'join_detect': self.join[i1].get(),
                'OK_jont': self.ok_vars[i1].get(),
                'NG_jont': self.ng_vars[i1].get(),
                'num_labels': int(self.num_inputs[i1].get()),
                'width_min': int(self.wn_inputs[i1].get()),
                'width_max': int(self.wx_inputs[i1].get()),
                'height_min': int(self.hn_inputs[i1].get()),
                'height_max': int(self.hx_inputs[i1].get()),
                'PLC_value': int(self.plc_inputs[i1].get()),
                'cmpnt_conf': int(self.conf_scales[i1].get()),
            }
            for i1 in range(len(self.model_name_labels))
        ]
        settings_dict = {setting['label_name']: setting for setting in model_settings}
        def check_label(i,settings_dict):
            width_result = table_results['xmax'][i] - table_results['xmin'][i]
            height_result = table_results['ymax'][i] - table_results['ymin'][i]
            conf_result = table_results['confidence'][i] * 100
            setting = settings_dict[table_results['name'][i]]
            if setting:
                if setting['join_detect']:
                    if width_result < setting['width_min'] or width_result > setting['width_max'] \
                            or height_result < setting['height_min'] or height_result > setting['height_max'] \
                            or conf_result < setting['cmpnt_conf']:
                        return i
                else:
                    return i
                return None
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = [executor.submit(check_label, i,settings_dict) for i in range(len(table_results.index))]
            label_remove = [f.result() for f in futures if f.result() is not None]
        table_results.drop(index=label_remove, inplace=True)
        name_rest = list(table_results['name'])
        for model_name,setting in settings_dict.items():
            if setting['join_detect'] and setting['OK_jont'] :
                    if  name_rest.count(model_name) != setting['num_labels']:
                        results_detect = 'NG'
                        ok_variable = True
                        list_label_ng.append(model_name)
            if setting['join_detect'] and setting['NG_jont'] :
                    if setting['label_name']  in name_rest:
                        results_detect = 'NG'
                        ok_variable = True
                        list_label_ng.append(model_name)
        if not ok_variable:
            results_detect = 'OK'
        show_img = np.squeeze(results.render(label_remove))
        show_img = cv2.resize(show_img, (width, height), interpolation=cv2.INTER_AREA)
        if cls:
            self._make_cls(input_image_original,results,model_settings)
        return show_img, results_detect, list_label_ng
