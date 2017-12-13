using UnityEngine;
using System;
using System.Collections;
using Amazon;
using Amazon.Runtime;
using Amazon.CognitoIdentity;
using Amazon.SQS;
using UnityEngine.UI;

public class SQSBridge : MonoBehaviour {

	Camera[] cams;
	private string queueUrl = "";// SQS Queue URL
	private string IdentityPoolId = "";// Identity Pool ID (Removed for security)

	public string CognitoIdentityRegion = RegionEndpoint.USEast1.SystemName;

	private RegionEndpoint _CognitoIdentityRegion
	{
		get { return RegionEndpoint.GetBySystemName(CognitoIdentityRegion); }
	}

	public string SQSRegion = RegionEndpoint.USEast1.SystemName;

	private RegionEndpoint _SQSRegion
	{
		get { return RegionEndpoint.GetBySystemName(SQSRegion); }
	}


	private AWSCredentials _credentials;

	private AWSCredentials Credentials
	{
		get
		{
			if (_credentials == null)
				_credentials = new CognitoAWSCredentials(IdentityPoolId, _CognitoIdentityRegion);
			return _credentials;
		}
	}

	private IAmazonSQS _sqsClient;

	private IAmazonSQS SqsClient {
		get {
			if (_sqsClient == null)
				_sqsClient = new AmazonSQSClient (Credentials, _SQSRegion);
			return _sqsClient;
		}
	}
	void Start () {
		cams = Camera.allCameras;
		UnityInitializer.AttachToGameObject(this.gameObject);
		Amazon.AWSConfigs.HttpClient = Amazon.AWSConfigs.HttpClientOption.UnityWebRequest;
		StartCoroutine(RepeatRetrieveMessage(0.1F));
		activateCam (2);// set
	}




	IEnumerator RepeatRetrieveMessage(float waitTime) {
		bool checkSQS = true;
		while (checkSQS) 
		{
			yield return new WaitForSeconds(waitTime);

			if (!string.IsNullOrEmpty (queueUrl)) {
				SqsClient.ReceiveMessageAsync (queueUrl, (result) => {
					if (result.Exception == null) {
						//Read the message
						var messages = result.Response.Messages;
						messages.ForEach (m => {

							RemoteCommand command = RemoteCommand.CreateFromJSON( m.Body );
							Debug.Log(@"Target " + command.target );
							int index = Int32.Parse(command.target);
							activateCam(index);
							Debug.Log(@"Done switching camera");

							//Delete the message
							var delRequest = new Amazon.SQS.Model.DeleteMessageRequest {
								QueueUrl = queueUrl,
								ReceiptHandle = m.ReceiptHandle

							};

							SqsClient.DeleteMessageAsync (delRequest, (delResult) => {
								if (delResult.Exception == null) {
								} else {
								}
							});


							Debug.Log(@"Done processing message ");

						});

					} else {
						Debug.Log( result.Exception );
						Debug.LogException (result.Exception);
					}


				});
			} else {
				Debug.Log (@"Queue Url is empty, make sure that the queue is created first");
			}
				
		}
	}


	void activateCam(int index)
	{
		disableAllCams ();
		cams [index].enabled = true;
	}

	void disableAllCams()
	{
		for (int i = 0; i < cams.Length; i++)
			cams [i].enabled = false;
	}
}
