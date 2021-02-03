#include <iostream>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

#include "rclcpp/rclcpp.hpp"
#include "geometry_msgs/msg/pose.hpp"
#include "sensor_msgs/msg/image.hpp"
#include "std_msgs/msg/header.hpp"

#include <opencv2/aruco.hpp>
//#include "visualization_msgs/msg/Marker.hpp"
//#include "visualization_msgs/msg/MarkerArray.hpp" 

#include <opencv2/imgproc/imgproc.hpp>
#include <opencv2/highgui/highgui.hpp>
#include <cv_bridge/cv_bridge.h>

using std::placeholders::_1;
using namespace std;
using namespace cv;

cv::Mat cameraMatrix, distCoeffs;
std::vector<int> markerIds;
std::vector<std::vector<cv::Point2f>> markerCorners, rejectedCandidates;
cv::Ptr<cv::aruco::Dictionary> dictionary = cv::aruco::getPredefinedDictionary(cv::aruco::DICT_6X6_50);

class MinimalSubscriber : public rclcpp::Node
{
  public:
    MinimalSubscriber()
    : Node("minimal_subscriber")
    {
      subscription_ = this->create_subscription<sensor_msgs::msg::Image>(
      "/zenith_camera/image_raw", 10, std::bind(&MinimalSubscriber::image_callback, this, _1));
    }

  private:
    void image_callback(const sensor_msgs::msg::Image::SharedPtr msg) const
    {
		std_msgs::msg::Header msg_header = msg->header;
		std::string frame_id = msg_header.frame_id.c_str();

		cv_bridge::CvImagePtr cv_ptr;
		try
		{
			cv_ptr = cv_bridge::toCvCopy(msg, sensor_msgs::image_encodings::BGR8);
			Mat frame = cv_ptr->image;
			cv::Mat frameCopy;
    		frame.copyTo(frameCopy);
			
   //  		// detection du marker 0
			// float x_t, y_t, z_t;
		 //    long int index;
		 //    float roll,yaw,pitch;
		 //    std::vector<cv::Vec3d> rvecs, tvecs;
/*
		    cv::aruco::detectMarkers(frame, dictionary, markerCorners, markerIds);
		    visualization_msgs::MarkerArray marker_array_msg;
		    marker_array_msg.markers.resize(2);

		    for(int i =0; i < marker_array_msg.markers.size(); i++){
		            marker_array_msg.markers[i].header.frame_id = "camera";
		            marker_array_msg.markers[i].header.stamp = ros::Time();
		            marker_array_msg.markers[i].id = -1;
		            marker_array_msg.markers[i].lifetime = ros::Duration();
		    }

		    // tracé des arucos sur l'image
		    if (markerIds.size() > 0) {
      			  cv::aruco::drawDetectedMarkers(frameCopy, markerCorners, markerIds,cv::Scalar(255, 0, 0));
      		}
*/			
			imshow("Entrée",frame);
			waitKey(3);

		}
		catch (cv_bridge::Exception& e)
		{
			RCLCPP_ERROR(this->get_logger(),"cv_bridge exception: %s", e.what());
			return;
    	}
    }
    rclcpp::Subscription<sensor_msgs::msg::Image>::SharedPtr subscription_;
};


int main(int argc, char * argv[])
{
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<MinimalSubscriber>());
  rclcpp::shutdown();
  return 0;
}