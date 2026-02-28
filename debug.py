class debug:
    def Update(self, dt):
        if self.parent.Rigidbody.velocity.magnitude() == 0:
            print(self.parent.position)
            self.Active = False