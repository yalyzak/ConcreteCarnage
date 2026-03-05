class debug:
    def Start(self):
        self.timepass = 0
    def Update(self, dt):
        # print(self.parent.Rigidbody.velocity.z)
        self.timepass += dt
        # if self.parent.position.z >=5:
        #     print(self.timepass, self.parent.Rigidbody.velocity.z)
        #     self.Active = False
        if self.parent.Rigidbody.velocity.magnitude() == 0:
            pass
            # self.parent.Rigidbody.velocity.z += self.timepass * 0.01
        else:
            print("asd", self.parent.Rigidbody.velocity.magnitude())

class debug2:
    def Start(self):
        self.timepass = 0
    def Update(self, dt):
        # print(self.parent.Rigidbody.velocity.z)
        self.timepass += dt
        # if self.parent.position.z >=5:
        #     print(self.timepass, self.parent.Rigidbody.velocity.z)
        #     self.Active = False
        if self.parent.Rigidbody.velocity.magnitude() == 0 and self.timepass > 5:
            print(self.parent.position)
            # self.parent.Rigidbody.velocity.z += 5
            self.Active = False
            print("add")