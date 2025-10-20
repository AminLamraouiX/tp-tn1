import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk
import numpy as np
import os
import math

class ColorSpaceConverter:
    def __init__(self, root):
        self.root = root
        self.root.title("TP NM1")
        self.root.geometry("1000x700")
        
        # إنشاء إطار رئيسي مع شريط تمرير
        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # إنشاء Canvas وشريط التمرير
        self.canvas = tk.Canvas(self.main_frame)
        self.scrollbar = ttk.Scrollbar(self.main_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # ربط حدث عجلة الماوس للتمرير
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)
        self.scrollable_frame.bind("<MouseWheel>", self._on_mousewheel)
        
        # متغيرات البرنامج
        self.image_path = None
        self.original_image = None
        self.current_image = None
        self.photo = None
        self.conversion_type = tk.StringVar(value="RGB")
        self.hsl_display_mode = tk.StringVar(value="single")
        
        # مصفوفات التحويل لـ XYZ (من الملف - الصفحة 4)
        self.M_RGB_to_XYZ = np.array([
            [2.769, 1.7518, 1.1300],
            [1.0000, 4.5907, 0.0601],
            [0.0000, 0.0565, 5.5943]
        ])
        
        # مصفوفة التحويل العكسي من XYZ إلى RGB
        self.M_XYZ_to_RGB = np.linalg.inv(self.M_RGB_to_XYZ)
        
        # متغيرات لتخزين الصور المحولة
        self.hsl_image = None
        self.xyz_image = None
        self.yuv_image = None
        self.original_hsl_array = None  # لتخزين HSL الأصلي
        
        # إنشاء واجهة المستخدم
        self.create_interface()
    
    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
    
    def create_interface(self):
        # إطار العنوان
        title_frame = tk.Frame(self.scrollable_frame)
        title_frame.pack(pady=10, fill=tk.X)
        
        tk.Label(title_frame, text="Lamraoui et Djemame", font=("Arial", 16, "bold")).pack()
        
        # إطار تحميل الصورة
        load_frame = tk.Frame(self.scrollable_frame)
        load_frame.pack(pady=10, fill=tk.X)
        
        tk.Button(load_frame, text="Upload image", command=self.load_image, 
                 bg="lightblue", font=("Arial", 10)).pack(side=tk.LEFT, padx=5)
        self.image_label = tk.Label(load_frame, text="No image uploaded", font=("Arial", 10))
        self.image_label.pack(side=tk.LEFT, padx=5)
        
        # إطار الصور (أصلي + محول)
        images_frame = tk.Frame(self.scrollable_frame)
        images_frame.pack(pady=10, fill=tk.X)
        
        # الصورة الأصلية
        original_frame = tk.LabelFrame(images_frame, text="Original Image", font=("Arial", 12, "bold"))
        original_frame.pack(side=tk.LEFT, padx=10, pady=5, fill=tk.BOTH, expand=True)
        
        self.original_canvas = tk.Canvas(original_frame, bg="lightgray", relief="solid", bd=1, width=400, height=300)
        self.original_canvas.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        
        # الصورة المحولة
        converted_frame = tk.LabelFrame(images_frame, text="Converted Image", font=("Arial", 12, "bold"))
        converted_frame.pack(side=tk.RIGHT, padx=10, pady=5, fill=tk.BOTH, expand=True)
        
        self.converted_canvas = tk.Canvas(converted_frame, bg="lightgray", relief="solid", bd=1, width=400, height=300)
        self.converted_canvas.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        
        # إطار معلومات البكسل تحت الصورة المحولة
        pixel_frame = tk.LabelFrame(converted_frame, text="Pixel Information", font=("Arial", 10, "bold"))
        pixel_frame.pack(padx=10, pady=5, fill=tk.X)

        self.pixel_info = tk.Label(pixel_frame, text="Click on the converted image to see pixel values",
                                  font=("Arial", 9), justify="left", wraplength=350)
        self.pixel_info.pack(pady=5)
        
        # ربط حدث النقر على الصورة المحولة
        self.converted_canvas.bind("<Button-1>", self.get_pixel_value)
        
        # إطار التحليل والتحويل
        controls_frame = tk.Frame(self.scrollable_frame)
        controls_frame.pack(pady=10, fill=tk.X)
        
        # زر التحليل
        analyze_frame = tk.Frame(controls_frame)
        analyze_frame.pack(side=tk.LEFT, padx=20)
        
        tk.Button(analyze_frame, text="تحليل RGB", command=self.analyze_rgb, 
                 bg="lightgreen", font=("Arial", 10), width=12).pack(pady=5)
        
        # زر تحويل XYZ إلى RGB
        tk.Button(analyze_frame, text="تحويل XYZ إلى RGB", command=self.convert_xyz_to_rgb_with_analysis, 
                 bg="lightcoral", font=("Arial", 10), width=15).pack(pady=5)
        
        # إطار التحويل
        convert_frame = tk.LabelFrame(controls_frame, text="System conversion", font=("Arial", 12, "bold"))
        convert_frame.pack(side=tk.LEFT, padx=20)
        
        tk.Label(convert_frame, text="Select System", font=("Arial", 10)).pack(pady=5)
        
        tk.Radiobutton(convert_frame, text="XYZ", variable=self.conversion_type, 
                      value="XYZ", font=("Arial", 10)).pack(anchor=tk.W)
        tk.Radiobutton(convert_frame, text="HSL", variable=self.conversion_type, 
                      value="HSL", font=("Arial", 10)).pack(anchor=tk.W)
        tk.Radiobutton(convert_frame, text="YUV", variable=self.conversion_type, 
                      value="YUV", font=("Arial", 10)).pack(anchor=tk.W)

        tk.Button(convert_frame, text="Convert", command=self.convert_image,
                 bg="orange", font=("Arial", 10), width=10).pack(pady=10)
        
        # إطار تعديل HSL وخيارات العرض
        self.hsl_frame = tk.LabelFrame(controls_frame, text="HSL Adjustment and Display Options", font=("Arial", 12, "bold"))
        
        hsl_input_frame = tk.Frame(self.hsl_frame)
        hsl_input_frame.pack(pady=10)
        
        # خيارات عرض HSL
        display_frame = tk.Frame(hsl_input_frame)
        display_frame.grid(row=0, column=0, columnspan=4, pady=5)

        tk.Label(display_frame, text="Display Mode:", font=("Arial", 10)).pack(side=tk.LEFT, padx=5)
        tk.Radiobutton(display_frame, text="Single Image", variable=self.hsl_display_mode,
                      value="single", font=("Arial", 9)).pack(side=tk.LEFT, padx=5)
        tk.Radiobutton(display_frame, text="3 Separate Channels", variable=self.hsl_display_mode,
                      value="channels", font=("Arial", 9)).pack(side=tk.LEFT, padx=5)
        
        # مدخلات HSL
        tk.Label(hsl_input_frame, text="H (-360 إلى +360):", font=("Arial", 10)).grid(row=1, column=0, padx=5, pady=5)
        self.h_entry = tk.Entry(hsl_input_frame, width=10, font=("Arial", 10))
        self.h_entry.grid(row=1, column=1, padx=5, pady=5)
        self.h_entry.insert(0, "0")
        
        tk.Label(hsl_input_frame, text="S (-100 إلى +100)%:", font=("Arial", 10)).grid(row=1, column=2, padx=5, pady=5)
        self.s_entry = tk.Entry(hsl_input_frame, width=10, font=("Arial", 10))
        self.s_entry.grid(row=1, column=3, padx=5, pady=5)
        self.s_entry.insert(0, "0")
        
        tk.Label(hsl_input_frame, text="L (-100 إلى +100)%:", font=("Arial", 10)).grid(row=1, column=4, padx=5, pady=5)
        self.l_entry = tk.Entry(hsl_input_frame, width=10, font=("Arial", 10))
        self.l_entry.grid(row=1, column=5, padx=5, pady=5)
        self.l_entry.insert(0, "0")
        
        # أزرار التحكم
        button_frame = tk.Frame(hsl_input_frame)
        button_frame.grid(row=2, column=0, columnspan=6, pady=10)
        
        tk.Button(button_frame, text="تطبيق التعديلات", command=self.apply_hsl, 
                 bg="lightcoral", font=("Arial", 10), width=15).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="عرض القنوات", command=self.show_hsl_channels, 
                 bg="lightyellow", font=("Arial", 10), width=15).pack(side=tk.LEFT, padx=5)
        
        # إطار قنوات RGB (سيظهر في الأسفل عند التحليل)
        self.rgb_frame = tk.LabelFrame(self.scrollable_frame, text="قنوات RGB", font=("Arial", 12, "bold"))
        
        channels_frame = tk.Frame(self.rgb_frame)
        channels_frame.pack(pady=10, fill=tk.X)
        
        # قناة R
        r_frame = tk.LabelFrame(channels_frame, text="قناة R (Red)", font=("Arial", 10))
        r_frame.pack(side=tk.LEFT, padx=5, pady=5, fill=tk.BOTH, expand=True)
        self.r_canvas = tk.Canvas(r_frame, bg="lightgray", relief="solid", bd=1, height=200)
        self.r_canvas.pack(padx=5, pady=5, fill=tk.BOTH, expand=True)
        
        # قناة G
        g_frame = tk.LabelFrame(channels_frame, text="قناة G (Green)", font=("Arial", 10))
        g_frame.pack(side=tk.LEFT, padx=5, pady=5, fill=tk.BOTH, expand=True)
        self.g_canvas = tk.Canvas(g_frame, bg="lightgray", relief="solid", bd=1, height=200)
        self.g_canvas.pack(padx=5, pady=5, fill=tk.BOTH, expand=True)
        
        # قناة B
        b_frame = tk.LabelFrame(channels_frame, text="قناة B (Blue)", font=("Arial", 10))
        b_frame.pack(side=tk.LEFT, padx=5, pady=5, fill=tk.BOTH, expand=True)
        self.b_canvas = tk.Canvas(b_frame, bg="lightgray", relief="solid", bd=1, height=200)
        self.b_canvas.pack(padx=5, pady=5, fill=tk.BOTH, expand=True)
        
        # إطار قنوات HSL (سيظهر عند الطلب)
        self.hsl_channels_frame = tk.LabelFrame(self.scrollable_frame, text="قنوات HSL", font=("Arial", 12, "bold"))
        
        hsl_channels_inner = tk.Frame(self.hsl_channels_frame)
        hsl_channels_inner.pack(pady=10, fill=tk.X)
        
        # قناة H
        h_frame = tk.LabelFrame(hsl_channels_inner, text="قناة H (Hue)", font=("Arial", 10))
        h_frame.pack(side=tk.LEFT, padx=5, pady=5, fill=tk.BOTH, expand=True)
        self.h_canvas = tk.Canvas(h_frame, bg="lightgray", relief="solid", bd=1, height=200)
        self.h_canvas.pack(padx=5, pady=5, fill=tk.BOTH, expand=True)
        
        # قناة S
        s_frame = tk.LabelFrame(hsl_channels_inner, text="قناة S (Saturation)", font=("Arial", 10))
        s_frame.pack(side=tk.LEFT, padx=5, pady=5, fill=tk.BOTH, expand=True)
        self.s_canvas = tk.Canvas(s_frame, bg="lightgray", relief="solid", bd=1, height=200)
        self.s_canvas.pack(padx=5, pady=5, fill=tk.BOTH, expand=True)
        
        # قناة L
        l_frame = tk.LabelFrame(hsl_channels_inner, text="قناة L (Lightness)", font=("Arial", 10))
        l_frame.pack(side=tk.LEFT, padx=5, pady=5, fill=tk.BOTH, expand=True)
        self.l_canvas = tk.Canvas(l_frame, bg="lightgray", relief="solid", bd=1, height=200)
        self.l_canvas.pack(padx=5, pady=5, fill=tk.BOTH, expand=True)
        
        # إطار قنوات XYZ (سيظهر عند الطلب)
        self.xyz_frame = tk.LabelFrame(self.scrollable_frame, text="قنوات XYZ", font=("Arial", 12, "bold"))
        
        xyz_channels_inner = tk.Frame(self.xyz_frame)
        xyz_channels_inner.pack(pady=10, fill=tk.X)
        
        # قناة X
        x_frame = tk.LabelFrame(xyz_channels_inner, text="قناة X", font=("Arial", 10))
        x_frame.pack(side=tk.LEFT, padx=5, pady=5, fill=tk.BOTH, expand=True)
        self.x_canvas = tk.Canvas(x_frame, bg="lightgray", relief="solid", bd=1, height=200)
        self.x_canvas.pack(padx=5, pady=5, fill=tk.BOTH, expand=True)
        
        # قناة Y
        y_frame = tk.LabelFrame(xyz_channels_inner, text="قناة Y", font=("Arial", 10))
        y_frame.pack(side=tk.LEFT, padx=5, pady=5, fill=tk.BOTH, expand=True)
        self.y_canvas = tk.Canvas(y_frame, bg="lightgray", relief="solid", bd=1, height=200)
        self.y_canvas.pack(padx=5, pady=5, fill=tk.BOTH, expand=True)
        
        # قناة Z
        z_frame = tk.LabelFrame(xyz_channels_inner, text="قناة Z", font=("Arial", 10))
        z_frame.pack(side=tk.LEFT, padx=5, pady=5, fill=tk.BOTH, expand=True)
        self.z_canvas = tk.Canvas(z_frame, bg="lightgray", relief="solid", bd=1, height=200)
        self.z_canvas.pack(padx=5, pady=5, fill=tk.BOTH, expand=True)
        
        # إطار قنوات YUV (سيظهر عند الطلب)
        self.yuv_frame = tk.LabelFrame(self.scrollable_frame, text="قنوات YUV", font=("Arial", 12, "bold"))
        
        yuv_channels_inner = tk.Frame(self.yuv_frame)
        yuv_channels_inner.pack(pady=10, fill=tk.X)
        
        # قناة Y
        y2_frame = tk.LabelFrame(yuv_channels_inner, text="قناة Y (Luminance)", font=("Arial", 10))
        y2_frame.pack(side=tk.LEFT, padx=5, pady=5, fill=tk.BOTH, expand=True)
        self.y2_canvas = tk.Canvas(y2_frame, bg="lightgray", relief="solid", bd=1, height=200)
        self.y2_canvas.pack(padx=5, pady=5, fill=tk.BOTH, expand=True)
        
        # قناة U
        u_frame = tk.LabelFrame(yuv_channels_inner, text="قناة U (Chrominance Blue)", font=("Arial", 10))
        u_frame.pack(side=tk.LEFT, padx=5, pady=5, fill=tk.BOTH, expand=True)
        self.u_canvas = tk.Canvas(u_frame, bg="lightgray", relief="solid", bd=1, height=200)
        self.u_canvas.pack(padx=5, pady=5, fill=tk.BOTH, expand=True)
        
        # قناة V
        v_frame = tk.LabelFrame(yuv_channels_inner, text="قناة V (Chrominance Red)", font=("Arial", 10))
        v_frame.pack(side=tk.LEFT, padx=5, pady=5, fill=tk.BOTH, expand=True)
        self.v_canvas = tk.Canvas(v_frame, bg="lightgray", relief="solid", bd=1, height=200)
        self.v_canvas.pack(padx=5, pady=5, fill=tk.BOTH, expand=True)
        
        # إخفاء الإطارات غير المستخدمة في البداية
        self.hsl_frame.pack_forget()
        self.rgb_frame.pack_forget()
        self.hsl_channels_frame.pack_forget()
        self.xyz_frame.pack_forget()
        self.yuv_frame.pack_forget()
    
    def load_image(self):
        file_path = filedialog.askopenfilename(
            title="اختر صورة",
            filetypes=[("Image files", "*.bmp *.png *.jpg *.jpeg")]
        )
        
        if file_path:
            try:
                self.image_path = file_path
                self.image_label.config(text=os.path.basename(file_path))
                
                # تحميل الصورة
                self.original_image = Image.open(file_path)
                self.current_image = self.original_image.copy()
                
                # عرض الصورة الأصلية
                self.display_image_resized(self.original_canvas, self.original_image)
                self.display_image_resized(self.converted_canvas, self.original_image)
                
                # إعادة تعيين متغيرات HSL
                self.original_hsl_array = None
                self.hsl_array = None
                
                # إخفاء الإطارات غير المستخدمة
                self.rgb_frame.pack_forget()
                self.hsl_channels_frame.pack_forget()
                self.xyz_frame.pack_forget()
                self.yuv_frame.pack_forget()
                
                messagebox.showinfo("تم", "تم تحميل الصورة بنجاح!")
                
            except Exception as e:
                messagebox.showerror("خطأ", f"تعذر تحميل الصورة: {str(e)}")
    
    def display_image_resized(self, canvas, image):
        canvas.delete("all")
        
        # الحصول على حجم Canvas
        canvas.update_idletasks()
        canvas_width = canvas.winfo_width()
        canvas_height = canvas.winfo_height()
        
        # إذا كان Canvas صغيراً جداً، نستخدم حجم افتراضي
        if canvas_width < 10:
            canvas_width = 400
        if canvas_height < 10:
            canvas_height = 300
        
        # تغيير حجم الصورة لتناسب Canvas مع الحفاظ على النسبة
        img_ratio = image.width / image.height
        canvas_ratio = canvas_width / canvas_height
        
        if img_ratio > canvas_ratio:
            # الصورة أوسع من Canvas
            new_width = canvas_width
            new_height = int(canvas_width / img_ratio)
        else:
            # الصورة أطول من Canvas
            new_height = canvas_height
            new_width = int(canvas_height * img_ratio)
        
        # التأكد من أن الأبعاد لا تقل عن 1
        new_width = max(1, new_width)
        new_height = max(1, new_height)
        
        # تغيير حجم الصورة
        resized_image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # تحويل الصورة إلى PhotoImage
        photo = ImageTk.PhotoImage(resized_image)
        
        # عرض الصورة في منتصف Canvas
        x = (canvas_width - new_width) // 2
        y = (canvas_height - new_height) // 2
        canvas.create_image(x, y, anchor=tk.NW, image=photo)
        
        # حفظ مرجع للصورة لمنع جمع القمامة
        canvas.photo = photo
        
        # حفظ معلومات الصورة المعروضة
        canvas.image = image
        canvas.resized_image = resized_image
        canvas.display_info = {
            'x': x, 
            'y': y, 
            'width': new_width, 
            'height': new_height,
            'scale_x': image.width / new_width,
            'scale_y': image.height / new_height
        }
    
    def analyze_rgb(self):
        if not self.original_image:
            messagebox.showerror("خطأ", "يرجى تحميل صورة أولاً!")
            return
        
        # عرض إطار قنوات RGB في الأسفل
        self.rgb_frame.pack(pady=10, padx=20, fill=tk.X)
        self.hsl_channels_frame.pack_forget()
        self.xyz_frame.pack_forget()
        self.yuv_frame.pack_forget()
        
        # تحويل الصورة إلى مصفوفة numpy
        if self.original_image.mode != 'RGB':
            img_array = np.array(self.original_image.convert('RGB'))
        else:
            img_array = np.array(self.original_image)
        
        # إنشاء قنوات R, G, B منفصلة
        r_channel = img_array.copy()
        r_channel[:, :, 1] = 0  # إزالة الأخضر
        r_channel[:, :, 2] = 0  # إزالة الأزرق
        
        g_channel = img_array.copy()
        g_channel[:, :, 0] = 0  # إزالة الأحمر
        g_channel[:, :, 2] = 0  # إزالة الأزرق
        
        b_channel = img_array.copy()
        b_channel[:, :, 0] = 0  # إزالة الأحمر
        b_channel[:, :, 1] = 0  # إزالة الأخضر
        
        # عرض القنوات
        r_image = Image.fromarray(r_channel)
        g_image = Image.fromarray(g_channel)
        b_image = Image.fromarray(b_channel)
        
        self.display_image_resized(self.r_canvas, r_image)
        self.display_image_resized(self.g_canvas, g_image)
        self.display_image_resized(self.b_canvas, b_image)
        
        # حفظ مرجع للصور المعروضة
        self.r_canvas.image = r_image
        self.g_canvas.image = g_image
        self.b_canvas.image = b_image
        
        # عرض الصورة الأصلية في الصورة المحولة
        self.display_image_resized(self.converted_canvas, self.original_image)
        self.converted_canvas.image = self.original_image
        
        # التمرير لأسفل لرؤية قنوات RGB
        self.canvas.yview_moveto(1)
        
        messagebox.showinfo("تحليل RGB", "تم تحليل الصورة وعرض قنوات RGB في الأسفل!")
    
    def convert_xyz_to_rgb_with_analysis(self):
        if not hasattr(self, 'xyz_array'):
            messagebox.showerror("خطأ", "يرجى تحويل الصورة إلى نظام XYZ أولاً!")
            return
        
        try:
            # تطبيق مصفوفة التحويل العكسي على كل بكسل
            rgb_array = np.zeros_like(self.xyz_array)
            for i in range(self.xyz_array.shape[0]):
                for j in range(self.xyz_array.shape[1]):
                    xyz = self.xyz_array[i, j, :3]
                    rgb = np.dot(self.M_XYZ_to_RGB, xyz)
                    # قص القيم إلى النطاق [0, 1] ثم تحويل إلى [0, 255]
                    rgb_clipped = np.clip(rgb, 0, 1)
                    rgb_array[i, j, :3] = rgb_clipped
            
            # تحويل المصفوفة إلى صورة
            rgb_display = (rgb_array * 255).astype(np.uint8)
            rgb_image = Image.fromarray(rgb_display)
            
            # عرض الصورة المحولة
            self.display_image_resized(self.converted_canvas, rgb_image)
            self.converted_canvas.image = rgb_image
            
            # الآن نقوم بتحليل RGB للصورة المحولة
            self.analyze_rgb_from_image(rgb_image)
            
            messagebox.showinfo("تحويل عكسي", "تم تحويل الصورة من XYZ إلى RGB وعرض قنوات RGB!")
            
        except Exception as e:
            messagebox.showerror("خطأ", f"فشل التحويل العكسي: {str(e)}")
    
    def analyze_rgb_from_image(self, image):
        """تحليل RGB لصورة معينة"""
        # عرض إطار قنوات RGB في الأسفل
        self.rgb_frame.pack(pady=10, padx=20, fill=tk.X)
        self.hsl_channels_frame.pack_forget()
        self.xyz_frame.pack_forget()
        self.yuv_frame.pack_forget()
        
        # تحويل الصورة إلى مصفوفة numpy
        if image.mode != 'RGB':
            img_array = np.array(image.convert('RGB'))
        else:
            img_array = np.array(image)
        
        # إنشاء قنوات R, G, B منفصلة
        r_channel = img_array.copy()
        r_channel[:, :, 1] = 0  # إزالة الأخضر
        r_channel[:, :, 2] = 0  # إزالة الأزرق
        
        g_channel = img_array.copy()
        g_channel[:, :, 0] = 0  # إزالة الأحمر
        g_channel[:, :, 2] = 0  # إزالة الأزرق
        
        b_channel = img_array.copy()
        b_channel[:, :, 0] = 0  # إزالة الأحمر
        b_channel[:, :, 1] = 0  # إزالة الأخضر
        
        # عرض القنوات
        r_image = Image.fromarray(r_channel)
        g_image = Image.fromarray(g_channel)
        b_image = Image.fromarray(b_channel)
        
        self.display_image_resized(self.r_canvas, r_image)
        self.display_image_resized(self.g_canvas, g_image)
        self.display_image_resized(self.b_canvas, b_image)
        
        # حفظ مرجع للصور المعروضة
        self.r_canvas.image = r_image
        self.g_canvas.image = g_image
        self.b_canvas.image = b_image
        
        # التمرير لأسفل لرؤية قنوات RGB
        self.canvas.yview_moveto(1)
    
    def convert_image(self):
        if not self.original_image:
            messagebox.showerror("خطأ", "يرجى تحميل صورة أولاً!")
            return
        
        conversion_type = self.conversion_type.get()
        
        if conversion_type == "XYZ":
            self.convert_to_xyz()
        elif conversion_type == "HSL":
            self.convert_to_hsl()
        elif conversion_type == "YUV":
            self.convert_to_yuv()
        else:
            messagebox.showwarning("نظام غير معروف", "نظام التحويل المختار غير معروف!")
    
    def convert_to_xyz(self):
        try:
            # تحويل الصورة إلى مصفوفة numpy
            if self.original_image.mode != 'RGB':
                img_array = np.array(self.original_image.convert('RGB')) / 255.0
            else:
                img_array = np.array(self.original_image) / 255.0
            
            # تطبيق مصفوفة التحويل على كل بكسل
            xyz_array = np.zeros_like(img_array)
            for i in range(img_array.shape[0]):
                for j in range(img_array.shape[1]):
                    rgb = img_array[i, j, :3]
                    xyz = np.dot(self.M_RGB_to_XYZ, rgb)
                    xyz_array[i, j, :3] = xyz
            
            # تخزين مصفوفة XYZ للتحويل العكسي
            self.xyz_array = xyz_array.copy()
            
            # إنشاء صور منفصلة لكل قناة من قنوات XYZ
            # قناة X
            x_channel = np.zeros_like(img_array)
            x_normalized = (xyz_array[:, :, 0] / np.max(xyz_array[:, :, 0]) * 255).astype(np.uint8)
            x_channel[:, :, 0] = x_normalized
            x_channel[:, :, 1] = x_normalized
            x_channel[:, :, 2] = x_normalized
            x_image = Image.fromarray(x_channel.astype(np.uint8))
            
            # قناة Y
            y_channel = np.zeros_like(img_array)
            y_normalized = (xyz_array[:, :, 1] / np.max(xyz_array[:, :, 1]) * 255).astype(np.uint8)
            y_channel[:, :, 0] = y_normalized
            y_channel[:, :, 1] = y_normalized
            y_channel[:, :, 2] = y_normalized
            y_image = Image.fromarray(y_channel.astype(np.uint8))
            
            # قناة Z
            z_channel = np.zeros_like(img_array)
            z_normalized = (xyz_array[:, :, 2] / np.max(xyz_array[:, :, 2]) * 255).astype(np.uint8)
            z_channel[:, :, 0] = z_normalized
            z_channel[:, :, 1] = z_normalized
            z_channel[:, :, 2] = z_normalized
            z_image = Image.fromarray(z_channel.astype(np.uint8))
            
            # عرض القنوات
            self.display_image_resized(self.x_canvas, x_image)
            self.display_image_resized(self.y_canvas, y_image)
            self.display_image_resized(self.z_canvas, z_image)
            
            # حفظ مرجع للصور المعروضة
            self.x_canvas.image = x_image
            self.y_canvas.image = y_image
            self.z_canvas.image = z_image
            
            # عرض إطار قنوات XYZ
            self.xyz_frame.pack(pady=10, padx=20, fill=tk.X)
            
            # إخفاء الإطارات الأخرى
            self.hsl_frame.pack_forget()
            self.hsl_channels_frame.pack_forget()
            self.yuv_frame.pack_forget()
            
            # عرض الصورة المحولة (القناة Y فقط كمثال)
            self.display_image_resized(self.converted_canvas, y_image)
            self.converted_canvas.image = y_image
            self.xyz_image = y_image
            
            # التمرير لأسفل لرؤية قنوات XYZ
            self.canvas.yview_moveto(1)
            
            messagebox.showinfo("تحويل XYZ", "تم تحويل الصورة إلى نظام XYZ وعرض القنوات!")
            
        except Exception as e:
            messagebox.showerror("خطأ", f"فشل التحويل إلى XYZ: {str(e)}")
    
    def rgb_to_hsl(self, r, g, b):
        """تحويل RGB إلى HSL باستخدام المعادلات من الصفحة 13"""
        # حساب القيمة (Value)
        v = (r + g + b) / 3.0
        
        # حساب التشبع (Saturation)
        min_val = min(r, g, b)
        if (r + g + b) == 0:
            s = 0
        else:
            s = 1 - (3 * min_val) / (r + g + b)
        
        # حساب الهوي (Hue)
        numerator = (r - g) + (r - b)
        denominator = 2 * math.sqrt((r - g)**2 + (r - b) * (g - b))
        
        if denominator == 0:
            theta = 0
        else:
            # تجنب القيم خارج النطاق [-1, 1] لدالة acos
            cos_theta = numerator / denominator
            cos_theta = max(-1.0, min(1.0, cos_theta))
            theta = math.acos(cos_theta)
        
        if b <= g:
            h = theta
        else:
            h = 2 * math.pi - theta
        
        # تحويل من راديان إلى درجات
        h_degrees = math.degrees(h)
        
        return h_degrees, s, v
    
    def hsl_to_rgb(self, h, s, v):
        """تحويل HSL إلى RGB"""
        h = math.radians(h)  # تحويل من درجات إلى راديان
        
        if s == 0:
            # إذا كان التشبع صفر، فاللون هو تدرج رمادي
            r = g = b = v
        else:
            # حساب القيم الوسيطة
            if v < 0.5:
                var_2 = v * (1 + s)
            else:
                var_2 = (v + s) - (s * v)
            
            var_1 = 2 * v - var_2
            
            # حساب RGB
            r = self.hue_to_rgb(var_1, var_2, h + (2 * math.pi / 3))
            g = self.hue_to_rgb(var_1, var_2, h)
            b = self.hue_to_rgb(var_1, var_2, h - (2 * math.pi / 3))
        
        return r, g, b
    
    def hue_to_rgb(self, v1, v2, vH):
        """مساعدة لتحويل Hue إلى RGB"""
        if vH < 0:
            vH += 2 * math.pi
        if vH > 2 * math.pi:
            vH -= 2 * math.pi
        
        if vH < math.pi / 3:
            return v1 + (v2 - v1) * 6 * vH / (2 * math.pi)
        elif vH < math.pi:
            return v2
        elif vH < 4 * math.pi / 3:
            return v1 + (v2 - v1) * (4 * math.pi / 3 - vH) * 6 / (2 * math.pi)
        else:
            return v1
    
    def convert_to_hsl(self):
        try:
            # تحويل الصورة إلى مصفوفة numpy
            if self.original_image.mode != 'RGB':
                img_array = np.array(self.original_image.convert('RGB')) / 255.0
            else:
                img_array = np.array(self.original_image) / 255.0
            
            # تحويل RGB إلى HSL يدوياً باستخدام المعادلات الصحيحة
            hsl_array = np.zeros_like(img_array)
            for i in range(img_array.shape[0]):
                for j in range(img_array.shape[1]):
                    r, g, b = img_array[i, j, :3]
                    h, s, v = self.rgb_to_hsl(r, g, b)
                    
                    hsl_array[i, j, 0] = h / 360.0  # تطبيع H إلى [0,1]
                    hsl_array[i, j, 1] = s
                    hsl_array[i, j, 2] = v
            
            # تخزين مصفوفة HSL الأصلية للتعديلات المستقبلية
            self.original_hsl_array = hsl_array.copy()
            self.hsl_array = hsl_array.copy()
            
            # تحويل HSL إلى RGB للعرض
            rgb_from_hsl = np.zeros_like(hsl_array)
            for i in range(hsl_array.shape[0]):
                for j in range(hsl_array.shape[1]):
                    h, s, v = hsl_array[i, j, :3]
                    h *= 360  # إعادة H إلى [0,360]
                    
                    r, g, b = self.hsl_to_rgb(h, s, v)
                    
                    rgb_from_hsl[i, j, 0] = max(0, min(1, r))
                    rgb_from_hsl[i, j, 1] = max(0, min(1, g))
                    rgb_from_hsl[i, j, 2] = max(0, min(1, b))
            
            # تطبيع القيم للعرض
            rgb_display = (rgb_from_hsl * 255).astype(np.uint8)
            
            # تحويل المصفوفة إلى صورة
            hsl_image = Image.fromarray(rgb_display)
            
            # عرض الصورة المحولة
            self.display_image_resized(self.converted_canvas, hsl_image)
            self.converted_canvas.image = hsl_image
            self.hsl_image = hsl_image
            
            # إظهار إطار HSL للتعديل
            self.hsl_frame.pack(side=tk.LEFT, padx=20)
            
            # إخفاء إطار قنوات HSL إذا كان ظاهراً
            self.hsl_channels_frame.pack_forget()
            self.xyz_frame.pack_forget()
            self.yuv_frame.pack_forget()
            
            messagebox.showinfo("تحويل HSL", "تم تحويل الصورة إلى نظام HSL!")
            
        except Exception as e:
            messagebox.showerror("خطأ", f"فشل التحويل إلى HSL: {str(e)}")
    
    def show_hsl_channels(self):
        if not hasattr(self, 'hsl_array'):
            messagebox.showerror("خطأ", "يرجى تحويل الصورة إلى نظام HSL أولاً!")
            return
        
        try:
            # استخدام مصفوفة HSL المخزنة من الصورة المحولة
            hsl_array = self.hsl_array
            
            # إنشاء صور منفصلة لكل قناة من قنوات HSL من الصورة المحولة
            # قناة H (Hue)
            h_channel = np.zeros((hsl_array.shape[0], hsl_array.shape[1], 3), dtype=np.uint8)
            h_normalized = (hsl_array[:, :, 0] * 255).astype(np.uint8)  # H كانت معيارية [0,1]
            h_channel[:, :, 0] = h_normalized
            h_channel[:, :, 1] = h_normalized
            h_channel[:, :, 2] = h_normalized
            h_image = Image.fromarray(h_channel)
            
            # قناة S (Saturation)
            s_channel = np.zeros((hsl_array.shape[0], hsl_array.shape[1], 3), dtype=np.uint8)
            s_normalized = (hsl_array[:, :, 1] * 255).astype(np.uint8)
            s_channel[:, :, 0] = s_normalized
            s_channel[:, :, 1] = s_normalized
            s_channel[:, :, 2] = s_normalized
            s_image = Image.fromarray(s_channel)
            
            # قناة L (Lightness)
            l_channel = np.zeros((hsl_array.shape[0], hsl_array.shape[1], 3), dtype=np.uint8)
            l_normalized = (hsl_array[:, :, 2] * 255).astype(np.uint8)
            l_channel[:, :, 0] = l_normalized
            l_channel[:, :, 1] = l_normalized
            l_channel[:, :, 2] = l_normalized
            l_image = Image.fromarray(l_channel)
            
            # عرض القنوات
            self.display_image_resized(self.h_canvas, h_image)
            self.display_image_resized(self.s_canvas, s_image)
            self.display_image_resized(self.l_canvas, l_image)
            
            # حفظ مرجع للصور المعروضة
            self.h_canvas.image = h_image
            self.s_canvas.image = s_image
            self.l_canvas.image = l_image
            
            # عرض إطار قنوات HSL
            self.hsl_channels_frame.pack(pady=10, padx=20, fill=tk.X)
            
            # التمرير لأسفل لرؤية قنوات HSL
            self.canvas.yview_moveto(1)
            
            messagebox.showinfo("عرض قنوات HSL", "تم عرض قنوات HSL المنفصلة من الصورة المحولة!")
            
        except Exception as e:
            messagebox.showerror("خطأ", f"فشل عرض قنوات HSL: {str(e)}")
    
    def apply_hsl(self):
        if not hasattr(self, 'original_hsl_array'):
            messagebox.showerror("خطأ", "يرجى تحويل الصورة إلى نظام HSL أولاً!")
            return
        
        try:
            h_val = float(self.h_entry.get()) if self.h_entry.get() else 0
            s_val = float(self.s_entry.get()) if self.s_entry.get() else 0
            l_val = float(self.l_entry.get()) if self.l_entry.get() else 0
            
            # البدء دائماً من HSL الأصلي وتطبيق التعديلات الجديدة عليه
            hsl_array = self.original_hsl_array.copy()
            
            # تطبيق التعديلات على مصفوفة HSL الأصلية
            for i in range(hsl_array.shape[0]):
                for j in range(hsl_array.shape[1]):
                    h, s, v = hsl_array[i, j, :3]
                    
                    # تطبيق التعديلات مع السماح بالقيم السالبة والموجبة
                    h_new = (h * 360 + h_val) % 360  # H: من -360 إلى +360
                    s_new = max(0, min(1, s + s_val/100.0))  # S: من -100 إلى +100 كنسبة مئوية
                    v_new = max(0, min(1, v + l_val/100.0))  # V: من -100 إلى +100 كنسبة مئوية
                    
                    hsl_array[i, j, 0] = h_new / 360.0  # تطبيع H إلى [0,1]
                    hsl_array[i, j, 1] = s_new
                    hsl_array[i, j, 2] = v_new
            
            # تحديث مصفوفة HSL الحالية
            self.hsl_array = hsl_array
            
            # تحويل HSL المعدل إلى RGB
            modified_rgb = np.zeros_like(hsl_array)
            for i in range(hsl_array.shape[0]):
                for j in range(hsl_array.shape[1]):
                    h, s, v = hsl_array[i, j, :3]
                    h *= 360  # إعادة H إلى [0,360]
                    
                    r, g, b = self.hsl_to_rgb(h, s, v)
                    
                    modified_rgb[i, j, 0] = max(0, min(1, r))
                    modified_rgb[i, j, 1] = max(0, min(1, g))
                    modified_rgb[i, j, 2] = max(0, min(1, b))
            
            # تطبيع القيم للعرض
            rgb_display = (modified_rgb * 255).astype(np.uint8)
            
            # تحويل المصفوفة إلى صورة
            modified_image = Image.fromarray(rgb_display)
            
            # عرض الصورة المعدلة
            self.display_image_resized(self.converted_canvas, modified_image)
            self.converted_canvas.image = modified_image
            self.hsl_image = modified_image
            
            # عرض قنوات HSL إذا كان الوضع channels مفعلاً
            if self.hsl_display_mode.get() == "channels":
                self.show_hsl_channels()
            
            messagebox.showinfo("تعديل HSL", "تم تطبيق تعديلات HSL على الصورة المحولة!")
            
        except ValueError:
            messagebox.showerror("خطأ", "يرجى إدخال قيم رقمية صحيحة!")
        except Exception as e:
            messagebox.showerror("خطأ", f"فشل تطبيق تعديلات HSL: {str(e)}")
    
    def convert_to_yuv(self):
        if not self.original_image:
            messagebox.showerror("خطأ", "يرجى تحميل صورة أولاً!")
            return
        
        try:
            # تحويل الصورة إلى مصفوفة numpy
            if self.original_image.mode != 'RGB':
                img_array = np.array(self.original_image.convert('RGB')) / 255.0
            else:
                img_array = np.array(self.original_image) / 255.0
            
            # تحويل RGB إلى YUV باستخدام معادلات الملف
            yuv_array = np.zeros_like(img_array)
            for i in range(img_array.shape[0]):
                for j in range(img_array.shape[1]):
                    r, g, b = img_array[i, j, :3]
                    
                    # حساب YUV باستخدام معادلات الملف
                    Y = 0.2989 * r + 0.5866 * g + 0.1145 * b
                    u = 0.5647 * (b - Y)
                    v = 0.7132 * (r - Y)
                    
                    yuv_array[i, j, 0] = Y
                    yuv_array[i, j, 1] = u
                    yuv_array[i, j, 2] = v
            
            # تخزين مصفوفة YUV
            self.yuv_array = yuv_array
            
            # تحويل YUV إلى RGB للعرض
            rgb_from_yuv = np.zeros_like(yuv_array)
            for i in range(yuv_array.shape[0]):
                for j in range(yuv_array.shape[1]):
                    Y, u, v = yuv_array[i, j, :3]
                    
                    # حساب RGB من YUV
                    r = Y + 1.403 * v
                    g = Y - 0.344 * u - 0.714 * v
                    b = Y + 1.770 * u
                    
                    rgb_from_yuv[i, j, 0] = max(0, min(1, r))
                    rgb_from_yuv[i, j, 1] = max(0, min(1, g))
                    rgb_from_yuv[i, j, 2] = max(0, min(1, b))
            
            # تطبيع القيم للعرض
            rgb_display = (rgb_from_yuv * 255).astype(np.uint8)
            
            # تحويل المصفوفة إلى صورة
            yuv_image = Image.fromarray(rgb_display)
            
            # عرض الصورة المحولة
            self.display_image_resized(self.converted_canvas, yuv_image)
            self.converted_canvas.image = yuv_image
            self.yuv_image = yuv_image
            
            # إنشاء صور منفصلة لكل قناة من قنوات YUV
            # قناة Y (Luminance)
            y_channel = np.zeros_like(img_array)
            y_normalized = (yuv_array[:, :, 0] * 255).astype(np.uint8)
            y_channel[:, :, 0] = y_normalized
            y_channel[:, :, 1] = y_normalized
            y_channel[:, :, 2] = y_normalized
            y_image = Image.fromarray(y_channel.astype(np.uint8))
            
            # قناة U (Chrominance Blue)
            u_channel = np.zeros_like(img_array)
            u_normalized = ((yuv_array[:, :, 1] + 0.5) * 255).astype(np.uint8)  # تطبيع إلى [0,255]
            u_channel[:, :, 0] = u_normalized
            u_channel[:, :, 1] = u_normalized
            u_channel[:, :, 2] = u_normalized
            u_image = Image.fromarray(u_channel.astype(np.uint8))
            
            # قناة V (Chrominance Red)
            v_channel = np.zeros_like(img_array)
            v_normalized = ((yuv_array[:, :, 2] + 0.5) * 255).astype(np.uint8)  # تطبيع إلى [0,255]
            v_channel[:, :, 0] = v_normalized
            v_channel[:, :, 1] = v_normalized
            v_channel[:, :, 2] = v_normalized
            v_image = Image.fromarray(v_channel.astype(np.uint8))
            
            # عرض القنوات
            self.display_image_resized(self.y2_canvas, y_image)
            self.display_image_resized(self.u_canvas, u_image)
            self.display_image_resized(self.v_canvas, v_image)
            
            # حفظ مرجع للصور المعروضة
            self.y2_canvas.image = y_image
            self.u_canvas.image = u_image
            self.v_canvas.image = v_image
            
            # عرض إطار قنوات YUV
            self.yuv_frame.pack(pady=10, padx=20, fill=tk.X)
            
            # إخفاء الإطارات الأخرى
            self.hsl_frame.pack_forget()
            self.hsl_channels_frame.pack_forget()
            self.xyz_frame.pack_forget()
            
            # التمرير لأسفل لرؤية قنوات YUV
            self.canvas.yview_moveto(1)
            
            messagebox.showinfo("تحويل YUV", "تم تحويل الصورة إلى نظام YUV وعرض القنوات!")
            
        except Exception as e:
            messagebox.showerror("خطأ", f"فشل التحويل إلى YUV: {str(e)}")
    
    def get_pixel_value(self, event):
        if not hasattr(self.converted_canvas, 'display_info'):
            return
        
        # الحصول على معلومات العرض
        display_info = self.converted_canvas.display_info
        
        # حساب إحداثيات البكسل في الصورة المعروضة
        x = event.x - display_info['x']
        y = event.y - display_info['y']
        
        # التأكد من أن النقر داخل الصورة
        if x < 0 or y < 0 or x >= display_info['width'] or y >= display_info['height']:
            return
        
        # تحويل الإحداثيات إلى الصورة المعروضة
        orig_x = int(x * display_info['scale_x'])
        orig_y = int(y * display_info['scale_y'])
        
        # الحصول على الصورة المعروضة حالياً
        current_displayed_image = self.converted_canvas.image
        
        # التأكد من أن الإحداثيات داخل الصورة
        if orig_x >= current_displayed_image.width or orig_y >= current_displayed_image.height:
            return
        
        # الحصول على قيم RGB من الصورة المعروضة حالياً
        if current_displayed_image.mode != 'RGB':
            rgb_pixel = current_displayed_image.convert('RGB').getpixel((orig_x, orig_y))
        else:
            rgb_pixel = current_displayed_image.getpixel((orig_x, orig_y))
        
        # حساب القيم الأخرى
        rgb_normalized = [c/255.0 for c in rgb_pixel[:3]]
        xyz_pixel = np.dot(self.M_RGB_to_XYZ, rgb_normalized)
        
        r, g, b = rgb_normalized
        h, s, v = self.rgb_to_hsl(r, g, b)
        
        Y = 0.2989 * r + 0.5866 * g + 0.1145 * b
        u = 0.5647 * (b - Y)
        v_val = 0.7132 * (r - Y)
        
        # عرض المعلومات
        pixel_info = f"البكسل ({orig_x}, {orig_y}) من الصورة المحولة:\n"
        pixel_info += f"RGB: ({rgb_pixel[0]}, {rgb_pixel[1]}, {rgb_pixel[2]})\n"
        pixel_info += f"XYZ: ({xyz_pixel[0]:.3f}, {xyz_pixel[1]:.3f}, {xyz_pixel[2]:.3f})\n"
        pixel_info += f"HSL: ({h:.1f}°, {s*100:.1f}%, {v*100:.1f}%)\n"
        pixel_info += f"YUV: (Y={Y:.3f}, U={u:.3f}, V={v_val:.3f})"
        
        self.pixel_info.config(text=pixel_info)

if __name__ == "__main__":
    root = tk.Tk()
    app = ColorSpaceConverter(root)
    root.mainloop()