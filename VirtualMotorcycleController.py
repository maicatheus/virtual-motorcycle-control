import cv2
import math
import time
import vgamepad as vg   
import mediapipe as mp

class VirtualMotorcycleController:
    def __init__(self):
        self.camera = cv2.VideoCapture(0)
        self.mp_draw = mp.solutions.drawing_utils
        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose()
        self.gamepad = vg.VX360Gamepad()
        
        self.speed = 0
        self.brake = 0
    
    @staticmethod
    def calculate_distance(point1, point2):
        return int(math.sqrt((point2[0] - point1[0]) ** 2 + (point2[1] - point1[1]) ** 2))
    
    @staticmethod
    def calculate_angle(point1, point2):
        theta = math.atan((point2[0] - point1[0])/(point2[1] - point1[1]))
        return int(theta*180/math.pi)
    
    @staticmethod
    def midpoint(point1, point2):
        return (int((point1[0] + point2[0]) / 2), int((point1[1] + point2[1]) / 2))
    
    @staticmethod
    def normalize_value( value, v_min, v_max):
        value = abs(value)

        if(value >= v_max):
            return 1
        if(value <= v_min):
            return 0

        return (value - v_min) / (v_max - v_min)
    
    def steering_control(self, angle):
        a_min, a_max = 1, 25
        steerling_error = 0.25
        multiple = 1

        if(angle>0):
            multiple = -1

        angle_normalized = self.normalize_value(angle, a_min, a_max)+steerling_error if self.normalize_value(angle, a_min, a_max)+steerling_error<=1 else 1.0
        
        self.gamepad.left_joystick_float(multiple*angle_normalized, 0)

    def control_speed(self,control_point,base_point):
        max_value_to_brake = 180
        max_value_to_speed_control = 160
        min_value_to_speed_control = 110

        distance_to_control_speed = self.calculate_distance(control_point,base_point)

        if distance_to_control_speed >= min_value_to_speed_control and distance_to_control_speed < max_value_to_speed_control:
            self.brake = 0
            self.speed = self.normalize_value(distance_to_control_speed,min_value_to_speed_control,max_value_to_speed_control) - 1
            print(self.speed)

        elif distance_to_control_speed >= max_value_to_speed_control:
            self.speed = 0
            self.brake = self.normalize_value(distance_to_control_speed,max_value_to_speed_control,max_value_to_brake)

        self.gamepad.right_trigger_float(-self.speed)
        self.gamepad.left_trigger_float(self.brake)

    def draw_rectangle_of_speed(self, frame,text,mode,color, x_position):
        bar_x = x_position  
        bar_y = 100 
        bar_height = 300 
        bar_width = 20  

        cv2.rectangle(frame, (bar_x, bar_y), (bar_x + bar_width, bar_y + bar_height), (255, 255, 255), 2)

        filled_height = int(bar_height * mode*-1)

        cv2.rectangle(frame, (bar_x, bar_y + bar_height - filled_height), (bar_x + bar_width, bar_y + bar_height), color, cv2.FILLED)

        cv2.putText(frame, f"{text}: {int(mode*-1 * 100)}", (bar_x - 40, bar_y + bar_height + 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

    def run(self):
        while True:
            ret, frame = self.camera.read()
            if not ret:
                print("Failed to grab frame")
                break
            
            frame = cv2.flip(frame, 1)
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.pose.process(frame_rgb)
            body = []

            if results.pose_landmarks:
                h, w, _ = frame.shape
                body = [(int(lm.x * w), int(lm.y * h)) for lm in results.pose_landmarks.landmark]
                self.mp_draw.draw_landmarks(frame, results.pose_landmarks, self.mp_pose.POSE_CONNECTIONS)
                
                try:
                                        
                    mid_point = self.midpoint(body[24], body[23])
                    
                    cv2.line(frame,mid_point,body[0],(255,0,0),2)

                    angle = self.calculate_angle(mid_point, body[0])

                    # self.steering_control(angle)
                    
                    self.control_speed(body[0], mid_point)

                    self.steering_control(angle)

                    cv2.putText(frame, f"Angle: {angle}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
                    self.draw_rectangle_of_speed(frame,"Speed", self.speed,(0,255,0),500)
                    self.draw_rectangle_of_speed(frame,"Brake", -self.brake,(0,0,255),100)
                             
                except Exception as e:
                    print(f"Error processing landmarks: {e}")

            cv2.imshow("Virtual Motorcycle Controller", frame)
            self.gamepad.update()
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        
        self.camera.release()
        cv2.destroyAllWindows()